from rdflib.term import Variable
from rdflib.plugins.sparql.evaluate import evalBGP, evalFilter, evalOrderBy, evalGroup, evalUnion, evalMinus, evalMultiset, evalAggregateJoin, evalReduced, evalDistinct, evalSlice, evalExtend, evalJoin, evalLeftJoin, evalAskQuery, evalProject
from itertools import tee
from utils.util import contains_regex
from utils.hash import hash_to_u64

class StageExtracter:
    def __init__(self):
        self.stage_vals = {}
        self.stage_counter = 1
    
    def get_stage_vals(self):
        return self.stage_vals

    def process_bgp(self, ctx, input):
        vals_arr = []
        # processed_triples = [
        #     tuple(None if isinstance(item, Variable) else item for item in triple)
        #     for triple in input.triples
        # ]
        # for triple in processed_triples:
        #     vals = ctx.graph.triples((triple))
        #     for val in vals:
        #         s, p, o = val
        #         vals_arr.append((str(s), str(p), str(o)))
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
        if stage_name == "BGP":
            vals = self.process_bgp_vars(ctx, condition)
            expression = {
                'p': vals,
                'op': 'bgp',
            }
        
        elif stage_name == "Filter":
            if contains_regex(condition.name):
                expression = {
                    'expr': str(condition['text']),
                    'op': str('regex_' + condition['flags']),
                    'value': str(condition['pattern'])
                }
            else:
                expression = {
                    'expr': str(condition['expr']),
                    'op': str(condition['op']),
                    'value': str(condition['other'])
                }

        elif stage_name == "OrderBy":
            flag = 1
            expression = {}
            for c in condition:
                expression[str(flag)] = {
                    'expr': str(c['expr']),
                    'op': 'order',
                    'value': c['order']
                }
                flag += 1

        elif stage_name == "Union":
            val_p1 = self.stage_vals[str(self.stage_counter - 2)]['value']
            val_p2 = self.stage_vals[str(self.stage_counter - 1)]['value']

            expression = {
                'p1': val_p1,
                'op': 'union',
                'p2': val_p2
            }

        elif stage_name == "Slice":
            start = condition.start
            length = condition.length

            expression = {
                'start': start,
                'op': 'slice',
                'len': length
            }
        
        elif stage_name == "Group":
            groups = []
            for c in condition:
                groups.append(str(c))

            expression = {
                'groupby': groups,
                'op': 'groupby',
                'value': None
            }

        elif stage_name == "AggregateJoin":
            previous_op = self.stage_vals[str(self.stage_counter - 1)] # should be 'Group'

            if previous_op['name'] != "Group":
                raise TypeError("Error: Must be 'Group' stage")
            
            before = previous_op['value']
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
                "value": before
            }

        elif stage_name == "Distinct":
            expression = {
                "expr": None,
                "op": "distinct",
                "value": None
            }

        elif stage_name == "LeftJoin":
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

        elif stage_name == "Minus":
            p2 = condition
            p2_bgp = self.process_bgp_vars(ctx, p2)

            expression = {
                'p1': None,
                'op': None,
                'p2': p2_bgp
            }

        elif stage_name == "AskQuery":
            expression = {
                'pv': [str(var) for var in condition.PV],
                'op': 'ask'
            }

        elif stage_name == "Project":
            expression = {
                'pv': [str(var) for var in condition.PV],
                'op': 'project'
            }

        elif stage_name == "Extend":
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

    def customEval(self, ctx, part):  # noqa: N802
        """
        Rewrite triple patterns to get super-classes
        """
        if part.name == "BGP":
            bgp = []
            generator = evalBGP(ctx, part.triples)
            gen1, gen2 = tee(generator, 2)
            for v in gen1:
                bgp.append(v)

            self.add_stage(ctx, part.name, part, bgp)
            
            return gen2
        
        if part.name == "Filter":
            filtered = []
            generator = evalFilter(ctx, part)
            gen1, gen2 = tee(generator, 2)

            for v in gen1:
                filtered.append(v)

            self.add_stage(ctx, part.name, part.expr, filtered)

            return gen2
        
        if part.name == "OrderBy":
            orderby = []
            generator = evalOrderBy(ctx, part)
            gen1, gen2 = tee(generator, 2)

            for v in gen1:
                orderby.append(v)
            
            self.add_stage(ctx, part.name, part.expr, orderby)

            return gen2
        
        if part.name == "Group":
            groupby = []
            generator = evalGroup(ctx, part)
            gen1, gen2 = tee(generator, 2)

            for v in gen1:
                groupby.append(v)

            self.add_stage(ctx, part.name, part.expr, groupby)

            return gen2
        
        if part.name == "Union":
            union = []
            generator = evalUnion(ctx, part)
            gen1, gen2 = tee(generator, 2)

            for v in gen1:
                union.append(v)

            self.add_stage(ctx, part.name, [part.p1, part.p2], union)

            return gen2
        
        if part.name == "Minus":
            minus = []
            generator = evalMinus(ctx, part)
            gen1, gen2 = tee(generator, 2)

            for v in gen1:
                minus.append(v)

            self.add_stage(ctx, part.name, part.p2, minus)

            return gen2
        
        if part.name == "ToMultiSet":
            intersect = []
            generator = evalMultiset(ctx, part)
            gen1, gen2 = tee(generator, 2)

            for v in gen1:
                intersect.append(v)

            self.add_stage(ctx,part.name, part.expr, intersect)

            return gen2
        
        if part.name == "AggregateJoin":
            aggregate = []
            generator = evalAggregateJoin(ctx, part)
            gen1, gen2 = tee(generator, 2)

            for v in gen1:
                aggregate.append(v)

            self.add_stage(ctx, part.name, part.A, aggregate)

            return gen2
        
        if part.name == "Reduced":
            reduced = []
            generator = evalReduced(ctx, part)
            gen1, gen2 = tee(generator, 2)

            for v in gen1:
                reduced.append(v)

            self.add_stage(ctx, part.name, part.expr, reduced)

            return gen2
        
        if part.name == "Distinct":
            distinct = []
            generator = evalDistinct(ctx, part)
            gen1, gen2 = tee(generator, 2)

            for v in gen1:
                distinct.append(v)

            self.add_stage(ctx, part.name, part, distinct)

            return gen2
        
        if part.name == "Slice":
            slice = []
            generator = evalSlice(ctx, part)
            gen1, gen2 = tee(generator, 2)

            for v in gen1:
                slice.append(v)

            self.add_stage(ctx, part.name, part, slice)

            return gen2
        
        if part.name == "Join":
            join = []
            generator = evalJoin(ctx, part)
            gen1, gen2 = tee(generator, 2)

            for v in gen1:
                join.append(v)

            self.add_stage(ctx, part.name, [part.p1, part.p2], join)

            return gen2
        
        if part.name == "LeftJoin":
            leftjoin = []
            generator = evalLeftJoin(ctx, part)
            gen1, gen2 = tee(generator, 2)

            for v in gen1:
                leftjoin.append(v)

            self.add_stage(ctx, part.name, part, leftjoin)

            return gen2
        
        if part.name == "Extend":
            extend = []
            generator = evalExtend(ctx, part)
            gen1, gen2 = tee(generator, 2)

            for v in gen1:
                extend.append(v)

            self.add_stage(ctx, part.name, part, extend)

            return gen2
        
        if part.name == "AskQuery":
            # Due to ASK query does not return actual values, so return an empty result
            self.add_stage(ctx, part.name, part, [{}])

            return evalAskQuery(ctx, part)
        
        if part.name == "Project":
            project = []
            generator = evalProject(ctx, part)
            gen1, gen2 = tee(generator, 2)

            for v in gen1:
                project.append(v)

            self.add_stage(ctx, part.name, part, project)

            return gen2

        raise NotImplementedError()