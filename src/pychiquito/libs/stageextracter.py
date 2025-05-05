from rdflib.term import Variable
from rdflib.plugins.sparql.evaluate import evalBGP, evalFilter, evalOrderBy, evalGroup, evalUnion, evalMinus, evalMultiset, evalAggregateJoin, evalReduced, evalDistinct, evalSlice, evalExtend, evalJoin, evalLeftJoin, evalAskQuery, evalProject, evalPart
from itertools import tee
from utils.util import contains_regex, constains_builtin
from enums.stages import QueryExecutionStage, QueryType

class StageExtracter:
    def __init__(self):
        self.stage_vals = {}
        self.stage_counter = 1
    
    def get_stage_vals(self):
        return self.stage_vals

    def process_bgp(self, ctx, input):
        vals_arr = []

        for triple in input.triples:
            new_triple = []
            var_positions = {}  # maps index to variable name

            for i, el in enumerate(triple):
                if isinstance(el, Variable):
                    new_triple.append(None)
                    var_positions[i] = el  # keep track of the variable
                else:
                    new_triple.append(el)

            # Query the graph
            for result in ctx.graph.triples(tuple(new_triple)):
                mapped_result = [None, None, None]

                for i in range(3):
                    if i in var_positions:
                        # Store value in position of variable
                        mapped_result[i] = result[i]
                    else:
                        mapped_result[i] = triple[i]

                vals_arr.append(tuple(mapped_result))
        
        return vals_arr
    
    def process_bgp_vars(self, ctx, input):
        vals_arr = set()

        for triple in input.triples:
            new_triple = []
            var_positions = {}  # maps index to variable name

            for i, el in enumerate(triple):
                if isinstance(el, Variable):
                    new_triple.append(None)
                    var_positions[i] = el  # keep track of the variable
                else:
                    new_triple.append(el)

            # Query the graph
            for result in ctx.graph.triples(tuple(new_triple)):
                for j in var_positions:
                    vals_arr.add((var_positions[j], result[j]))

        return vals_arr

    def add_stage(self, ctx, stage_name, condition, values):
        expression = {}
        val_arr = []

        # Process expression
        match stage_name:
            case QueryExecutionStage.BGP.value:
                vals = self.process_bgp_vars(ctx, condition)
                expression = {
                    'p': vals,
                    'op': 'bgp',
                }
            
            case QueryExecutionStage.FILTER.value:
                # Prove the values before going through the filter
                previous_op = self.stage_vals[str(self.stage_counter - 1)]
                prev_values = previous_op['value']

                # TODO: Handle more than 1 filter and "ConditionalAndExpression" type
                if contains_regex(condition.name):
                    expression = {
                        'expr': str(condition['text']),
                        'op': str('regex_' + condition['flags']),
                        'value': str(condition['pattern'])
                    }
                elif constains_builtin(condition.name):
                    p2 = condition.graph.p2
                    if p2.name == QueryExecutionStage.BGP.value:
                        condition_val = self.process_bgp_vars(ctx, p2)
                        expression = {
                            'expr': condition._vars,
                            'op': condition.name,
                            'value': condition_val
                        }
                else:
                    if hasattr(condition['expr'], 'name') and condition['expr'].name == 'Function':
                        # TODO: At present, just focus on 1 variable for the experiment
                        # In the future, must address more
                        cond = str(condition['expr'].expr[0])
                    else:
                        cond = str(condition['expr'])
                    expression = {
                        'expr': cond,
                        'op': str(condition['op']),
                        'value': str(condition['other']),
                        'prev_value': prev_values
                    }

            case QueryExecutionStage.ORDER_BY.value:
                flag = 1
                expression = {}
                for c in condition:
                    expression[str(flag)] = {
                        'expr': str(c['expr']),
                        'op': 'order',
                        'value': c['order']
                    }
                    flag += 1

            case QueryExecutionStage.UNION.value:
                val_p1 = self.stage_vals[str(self.stage_counter - 2)]['value']
                val_p2 = self.stage_vals[str(self.stage_counter - 1)]['value']

                expression = {
                    'p1': val_p1,
                    'op': 'union',
                    'p2': val_p2
                }

            case QueryExecutionStage.SLICE.value:
                start = condition.start
                length = condition.length

                expression = {
                    'start': start,
                    'op': 'slice',
                    'len': length
                }
            
            case QueryExecutionStage.GROUP.value:
                groups = []
                values2group = []

                try:
                    prev_stage_vals = self.stage_vals[str(self.stage_counter - 1)]['value']
                    values2group = prev_stage_vals
                except:
                    print("Error: Failed to get the previous values to group.")
                
                for c in condition.expr:
                    groups.append(str(c))

                expression = {
                    'groupby': groups,
                    'op': 'groupby',
                    'value': values2group
                }

            case QueryExecutionStage.AGGREGATE.value:
                previous_op = self.stage_vals[str(self.stage_counter - 1)] # should be 'Group'

                if previous_op['name'] != "Group":
                    raise TypeError("Error: Must be 'Group' stage")
                
                prev_values = previous_op['value']
                # TODO: Check more than 3 groupby vars
                groupby = previous_op['condition']

                aggregate_arr = []
                for c in condition:
                    op_hash = {
                        "name": c.name,
                        "vars": str(c.vars),
                        "res": str(c.res)
                    }
                    aggregate_arr.append(op_hash)
                
                expression = {
                    "agg": aggregate_arr,
                    "op": groupby,
                    "value": prev_values
                }

            case QueryExecutionStage.DISTINCT.value:
                expression = {
                    "expr": None,
                    "op": "distinct",
                    "value": None
                }

            case QueryExecutionStage.OPTIONAL.value:
                p1 = condition['p1']
                p2 = condition['p2']
                op = condition['expr']

                if p1.name == "BGP":
                    p1_bgp = self.process_bgp_vars(ctx, p1)
                else:
                    p1_bgp = set()
                
                if p2.name == "BGP":
                    p2_bgp = self.process_bgp_vars(ctx, p2)
                else:
                    p2_bgp = set()

                expression = {
                    'p1': p1_bgp,
                    'op': op,
                    'p2': p2_bgp
                }

            case QueryExecutionStage.MINUS.value:
                p2 = condition
                p2_bgp = self.process_bgp_vars(ctx, p2)

                expression = {
                    'p1': None,
                    'op': None,
                    'p2': p2_bgp
                }

            case QueryType.ASK.value:
                expression = {
                    'pv': [str(var) for var in condition.PV],
                    'op': 'ask'
                }

            case QueryExecutionStage.PROJECT.value:
                expression = {
                    'pv': [str(var) for var in condition.PV],
                    'op': 'project'
                }

            case QueryExecutionStage.EXTEND.value:
                # Temporarily ignore extend, due to various forms
                var_target = condition['var']
                var_cal = condition.expr['expr'] if 'expr' in condition.expr else None
                op = condition.expr['op'] if 'op' in condition.expr else None
                extend_op_name = condition.expr.name if 'name' in condition.expr else None
                other = condition.expr['other'] if 'other' in condition.expr else None

                expression = {
                    'var_target': var_target,
                    'var_cal': var_cal,
                    'op': op,
                    'extend_op_name': extend_op_name,
                    'other': other
                }
            case _:
                raise NotImplementedError()

        # Process values
        for value in values:
            dict = {}
            for var, val in value.items():
                dict[str(var)] = str(val)
            val_arr.append(dict)

        self.stage_vals[str(self.stage_counter)] = {
            "name": stage_name,
            "condition": expression,
            "value": val_arr #[hash_to_u64(v) for v in val_arr]
        }
        self.stage_counter += 1

    def ZKPQueryEval(self, ctx, part):
        """
        Extract intermediate values at each stage
        """
        match part.name:
            case QueryExecutionStage.BGP.value:
                bgp = []
                generator = evalBGP(ctx, part.triples)
                gen1, gen2 = tee(generator, 2)
                for v in gen1:
                    bgp.append(v)

                self.add_stage(ctx, part.name, part, bgp)
                
                return gen2
            
            case QueryExecutionStage.FILTER.value:
                filtered = []
                generator = evalFilter(ctx, part)
                gen1, gen2 = tee(generator, 2)

                for v in gen1:
                    filtered.append(v)

                self.add_stage(ctx, part.name, part.expr, filtered)

                return gen2
            
            case QueryExecutionStage.ORDER_BY.value:
                orderby = []
                generator = evalOrderBy(ctx, part)
                gen1, gen2 = tee(generator, 2)

                for v in gen1:
                    orderby.append(v)
                
                self.add_stage(ctx, part.name, part.expr, orderby)

                return gen2
            
            case QueryExecutionStage.GROUP.value:
                groupby = []
                generator = evalGroup(ctx, part)
                gen1, gen2 = tee(generator, 2)

                for v in gen1:
                    groupby.append(v)

                self.add_stage(ctx, part.name, part, groupby)

                return gen2
            
            case QueryExecutionStage.UNION.value:
                union = []
                generator = evalUnion(ctx, part)
                gen1, gen2 = tee(generator, 2)

                for v in gen1:
                    union.append(v)

                self.add_stage(ctx, part.name, [part.p1, part.p2], union)

                return gen2
            
            case QueryExecutionStage.MINUS.value:
                minus = []
                generator = evalMinus(ctx, part)
                gen1, gen2 = tee(generator, 2)

                for v in gen1:
                    minus.append(v)

                self.add_stage(ctx, part.name, part.p2, minus)

                return gen2
            
            case QueryExecutionStage.TO_MULTISET.value:
                intersect = []
                generator = evalMultiset(ctx, part)
                gen1, gen2 = tee(generator, 2)

                for v in gen1:
                    intersect.append(v)

                self.add_stage(ctx,part.name, part.expr, intersect)

                return gen2
            
            case QueryExecutionStage.AGGREGATE.value:
                aggregate = []
                generator = evalAggregateJoin(ctx, part)
                gen1, gen2 = tee(generator, 2)

                for v in gen1:
                    aggregate.append(v)

                self.add_stage(ctx, part.name, part.A, aggregate)

                return gen2
            
            case QueryExecutionStage.REDUCED.value:
                reduced = []
                generator = evalReduced(ctx, part)
                gen1, gen2 = tee(generator, 2)

                for v in gen1:
                    reduced.append(v)

                self.add_stage(ctx, part.name, part.expr, reduced)

                return gen2
            
            case QueryExecutionStage.DISTINCT.value:
                distinct = []
                generator = evalDistinct(ctx, part)
                gen1, gen2 = tee(generator, 2)

                for v in gen1:
                    distinct.append(v)

                self.add_stage(ctx, part.name, part, distinct)

                return gen2
            
            case QueryExecutionStage.SLICE.value:
                slice = []
                generator = evalSlice(ctx, part)
                gen1, gen2 = tee(generator, 2)

                for v in gen1:
                    slice.append(v)

                self.add_stage(ctx, part.name, part, slice)

                return gen2
            
            case QueryExecutionStage.JOIN.value:
                join = []
                generator = evalJoin(ctx, part)
                gen1, gen2 = tee(generator, 2)

                for v in gen1:
                    join.append(v)

                self.add_stage(ctx, part.name, [part.p1, part.p2], join)

                return gen2
            
            case QueryExecutionStage.OPTIONAL.value:
                leftjoin = []
                generator = evalLeftJoin(ctx, part)
                gen1, gen2 = tee(generator, 2)

                for v in gen1:
                    leftjoin.append(v)

                self.add_stage(ctx, part.name, part, leftjoin)

                return gen2
            
            case QueryExecutionStage.EXTEND.value:
                extend = []
                generator = evalExtend(ctx, part)
                gen1, gen2 = tee(generator, 2)

                for v in gen1:
                    extend.append(v)

                self.add_stage(ctx, part.name, part, extend)

                return gen2
            
            case QueryType.ASK.value:
                # Due to ASK query does not return actual values, so return an empty result
                self.add_stage(ctx, part.name, part, [{}])

                return evalAskQuery(ctx, part)
            
            case QueryExecutionStage.PROJECT.value:
                project = []
                generator = evalProject(ctx, part)
                gen1, gen2 = tee(generator, 2)

                for v in gen1:
                    project.append(v)

                self.add_stage(ctx, part.name, part, project)

                return gen2

            case _:
                raise NotImplementedError()