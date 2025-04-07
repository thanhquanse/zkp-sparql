mod chips;

use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::io::{self, BufRead};

use chrono::{DateTime, NaiveDate, Utc};
use halo2_proofs::dev::MockProver;
use std::marker::PhantomData;

use halo2curves::pasta::{pallas, vesta, EqAffine, Fp};

use halo2_proofs::{
    circuit::{Layouter, SimpleFloorPlanner, Value},
    plonk::{
        create_proof, keygen_pk, keygen_vk, verify_proof, Advice, Circuit, Column,
        ConstraintSystem, Error, Instance,
    },
    poly::{
        commitment::{Params, ParamsProver},
        ipa::{
            commitment::{IPACommitmentScheme, ParamsIPA},
            multiopen::ProverIPA,
            strategy::SingleStrategy,
        },
        VerificationStrategy,
    },
    transcript::{
        Blake2bRead, Blake2bWrite, Challenge255, TranscriptReadBuffer, TranscriptWriterBuffer,
    },
};
use rand::rngs::OsRng;
use std::collections::HashMap;
use std::time::Instant;
use std::{fs::File, io::Write, path::Path};

use halo2_proofs::{halo2curves::ff::PrimeField, plonk::Expression};
use crate::chips::permutation_any::{PermAnyChip, PermAnyConfig};
use crate::chips::is_zero::{IsZeroChip, IsZeroConfig};
use crate::chips::less_than::{LtChip, LtConfig, LtInstruction};
use crate::chips::lessthan_or_equal_generic::{
    LtEqGenericChip, LtEqGenericConfig, LtEqGenericInstruction,
};
use crate::chips::lessthan_or_equal_v1::{LtEqVecChip, LtEqVecConfig, LtEqVecInstruction};
use crate::chips::is_zero_v2::{IsZeroV2Chip, IsZeroV2Config};
use halo2_proofs::{circuit::*, plonk::*, poly::Rotation};
use std::env;

const NUM_BYTES: usize = 5;

pub trait Field: PrimeField<Repr = [u8; 32]> {}

impl<F> Field for F where F: PrimeField<Repr = [u8; 32]> {}

pub(crate) struct Graph {
    pub subject: String,
    pub predicate: String,
    pub object: String,
}

fn get_pwd() -> String {
    env::current_dir()
        .expect("Failed to get current directory")
        .to_string_lossy()
        .into_owned()
}

fn string_to_u64(s: &str) -> u64 {
    let mut hasher = DefaultHasher::new();
    s.hash(&mut hasher);
    hasher.finish()
}

pub(crate) fn create_graph(list: Vec<String>) -> Result<Vec<Graph>, std::fmt::Error> {
    let mut triples: Vec<Graph> = Vec::new();

    for triple in list {
        let fields: Vec<&str> = triple.split('|').collect();

        let record = Graph {
            subject: fields[0].to_string(),
            predicate: fields[1].to_string(),
            object: fields[2].to_string(),
        };

        triples.push(record);
    }

    Ok(triples)
}

#[derive(Clone, Debug)]
pub struct TestCircuitConfig<F: Field + Ord> {
    q_enable: Vec<Selector>,
    q_accu: Selector,
    q_sort: Vec<Selector>,
    q_perm: Vec<Selector>,

    graph_triples: Vec<Column<Advice>>,
    groupby: Vec<Column<Advice>>,

    subject_condition: Column<Advice>,

    actual_k_value: Column<Advice>,
    expected_k_value: Column<Advice>,
    sat_k_value: Column<Advice>,
    threshold_k_value: Column<Advice>,

    check: Vec<Column<Advice>>,
    equal_check: Column<Advice>,
    kvalue_check: Column<Advice>,

    equal_condition: Vec<IsZeroConfig<F>>,
    // compare_condition: Vec<LtEqGenericConfig<F, NUM_BYTES>>,
    instance: Column<Instance>,
    instance_test: Column<Advice>,
}

#[derive(Debug, Clone)]
pub struct TestChip<F: Field + Ord> {
    config: TestCircuitConfig<F>,
}

impl<F: Field + Ord> TestChip<F> {
    pub fn construct(config: TestCircuitConfig<F>) -> Self {
        Self { config }
    }

    pub fn configure(meta: &mut ConstraintSystem<F>) -> TestCircuitConfig<F> {
        let instance = meta.instance_column();
        meta.enable_equality(instance);
        let instance_test = meta.advice_column();
        meta.enable_equality(instance_test);

        let mut q_enable = Vec::new();
        let mut q_perm = Vec::new();
        let mut check = Vec::new();
        let mut is_zero_vectors = Vec::new();

        for i_ in 0..2 {
            q_enable.push(meta.selector());
            q_perm.push(meta.complex_selector());
            check.push(meta.advice_column());
            is_zero_vectors.push(meta.advice_column());
        }

        let q_accu = meta.selector();
        let mut q_sort = Vec::new();
        for _ in 0..1 {
            q_sort.push(meta.selector());
        }

        let mut graph_triples = Vec::new();
        let mut groupby = Vec::new();
        for _ in 0..3 {
            graph_triples.push(meta.advice_column());
            groupby.push(meta.advice_column());
        }

        let subject_condition = meta.advice_column();
        let expected_k_value = meta.advice_column();
        let actual_k_value = meta.advice_column();
        let sat_k_value = meta.advice_column();
        let threshold_k_value = meta.advice_column();

        let equal_check = meta.advice_column();
        let kvalue_check = meta.advice_column();

        // constraints for subject = :1
        let mut equal_condition = Vec::new();
        let config = IsZeroChip::configure(
            meta,
            |meta| meta.query_selector(q_enable[0]), // this is the q_enable
            |meta| {
                meta.query_advice(graph_triples[0], Rotation::cur())
                    - meta.query_advice(subject_condition, Rotation::cur())
            }, // this is the value
            is_zero_vectors[0], // this is the advice column that stores value_inv
        );
        equal_condition.push(config.clone());

        meta.create_gate("(1) f(a, b) = if a == b {1} else {0}", |meta| {
            let s = meta.query_selector(q_enable[0]);
            let output = meta.query_advice(check[0], Rotation::cur());
            vec![
                s.clone() * (config.expr() * (output.clone() - Expression::Constant(F::ONE))), // in this case output == 1
                s * (Expression::Constant(F::ONE) - config.expr()) * (output), // in this case output == 0
            ]
        });

        // constraints for object = :1
        let config = IsZeroChip::configure(
            meta,
            |meta| meta.query_selector(q_enable[0]), // this is the q_enable
            |meta| {
                meta.query_advice(graph_triples[2], Rotation::cur())
                    - meta.query_advice(subject_condition, Rotation::cur())
            }, // this is the value
            is_zero_vectors[1], // this is the advice column that stores value_inv
        );
        equal_condition.push(config.clone());

        meta.create_gate("(2) f(a, b) = if a == b {1} else {0}", |meta| {
            let s = meta.query_selector(q_enable[0]);
            let output = meta.query_advice(check[1], Rotation::cur());
            vec![
                s.clone() * (config.expr() * (output.clone() - Expression::Constant(F::ONE))), // in this case output == 1
                s * (Expression::Constant(F::ONE) - config.expr()) * (output), // in this case output == 0
            ]
        });

        // meta.create_gate("kvalue accumulate check", |meta| {
        //     let q_sort = meta.query_selector(q_sort[0]);
        //     let prev_kvalue = meta.query_advice(kvalue_check, Rotation::prev());
        //     let kvalue_check = meta.query_advice(kvalue_check, Rotation::cur());
        //     let equal_check = meta.query_advice(equal_check, Rotation::cur());
        //     vec![
        //         q_sort.clone()
        //             * (prev_kvalue * equal_check + Expression::Constant(F::ONE) - kvalue_check),
        //     ]
        // });

        // let mut compare_condition = Vec::new();

        // let config_lt = LtEqGenericChip::configure(
        //     meta,
        //     |meta| meta.query_selector(q_enable[1]),
        //     |meta| vec![meta.query_advice(threshold_k_value, Rotation::cur())],
        //     |meta| vec![meta.query_advice(expected_k_value, Rotation::cur())],
        // );
        // compare_condition.push(config_lt.clone());

        // let config_lt_1 = LtEqGenericChip::configure(
        //     meta,
        //     |meta| meta.query_selector(q_enable[1]),
        //     |meta| vec![meta.query_advice(expected_k_value, Rotation::cur())],
        //     |meta| vec![meta.query_advice(actual_k_value, Rotation::cur())],
        // );
        // compare_condition.push(config_lt_1);

        // meta.create_gate("verifies k value threshold", |meta| {
        //     let q_enable = meta.query_selector(q_enable[1]);

        //     let equal = meta.query_advice(expected_k_value, Rotation::cur())
        //         - meta.query_advice(actual_k_value, Rotation::cur());
        //     vec![
        //         q_enable.clone() * (config_lt.is_lt(meta, None) - Expression::Constant(F::ONE)),
        //         q_enable.clone() * (config_lt_1.is_lt(meta, None) - Expression::Constant(F::ONE)),
        //     ]
        // });

        // meta.create_gate("kvalue expected check", |meta| {
        //     let q_enable = meta.query_selector(q_enable[1]);
        //     let k_value_sat = meta.query_advice(sat_k_value, Rotation::cur());

        //     vec![q_enable * (k_value_sat - Expression::Constant(F::ONE))]
        // });

        TestCircuitConfig {
            q_enable,
            q_accu,
            q_sort,
            q_perm,
            graph_triples,
            groupby,
            subject_condition,
            expected_k_value,
            actual_k_value,
            threshold_k_value,

            // equal_v2,
            check,
            equal_check,
            kvalue_check,
            sat_k_value,
            // compare_condition,
            equal_condition,

            instance,
            instance_test,
        }
    }

    pub fn assign(
        &self,
        layouter: &mut impl Layouter<F>,
        graph_triples: Vec<Vec<u64>>,
        condition: Vec<u64>,
        expected_k_value: F,
    ) -> Result<AssignedCell<F, F>, Error> {
        let mut equal_chip = Vec::new();
        // let mut compare_chip = Vec::new();
        for i in 0..self.config.equal_condition.len() {
            let chip = IsZeroChip::construct(self.config.equal_condition[i].clone());
            equal_chip.push(chip);
        }
        // for i in 0..self.config.compare_condition.len() {
        //     let chip = LtEqGenericChip::construct(self.config.compare_condition[i].clone());
        //     chip.load(layouter)?;
        //     compare_chip.push(chip);
        // }

        let start = Instant::now();
        let mut s_check = Vec::new();
        let mut o_check = Vec::new();
        for i in 0..graph_triples.len() {
            if graph_triples[i][0] == condition[0] {
                s_check.push(F::from(1));
            } else {
                s_check.push(F::from(0));
            }

            if graph_triples[i][2] == condition[0] {
                o_check.push(F::from(1));
            } else {
                o_check.push(F::from(0));
            }
        }
        // for i in 0..graph_triples.len() {
        //     if graph_triples[i][2] == condition[0] {
        //         o_check.push(F::from(0));
        //     } else {
        //         o_check.push(F::from(0));
        //     }
        // }

        // let duration_block = start.elapsed();
        // println!("Time elapsed for block: {:?}", duration_block);

        // fn sort_vec_of_vecs(data: &mut Vec<Vec<u64>>) {
        //     // Sort each inner Vec<u64>
        //     for vec in data.iter_mut() {
        //         vec.sort();
        //     }
        //     data.sort();
        // }

        // fn sort_vec_of_tuples(data: &mut Vec<(u64, u64)>) {
        //     data.sort();
        // }

        // pub fn is_contained_vecs(outer: &Vec<Vec<u64>>, inner: &Vec<Vec<u64>>) -> bool {
        //     // Check if every inner Vec<u64> in `inner` is present in `outer`
        //     let outer_set: HashSet<_> = outer.iter().cloned().collect();
        //     inner.iter().all(|item| outer_set.contains(item))
        // }

        // fn is_contained_tuples(outer: &Vec<(u64, u64)>, inner: &Vec<(u64, u64)>) -> bool {
        //     // Convert outer Vec to a HashSet for fast lookup
        //     let outer_set: HashSet<_> = outer.iter().cloned().collect();

        //     // Check if every element in inner exists in outer_set
        //     inner.iter().all(|item| outer_set.contains(item))
        // }

        // let mut final_target_spo: Vec<Vec<u64>> = Vec::new();
        // let mut equal_check: Vec<F> = Vec::new();
        // let mut k_value_proof: Vec<F> = Vec::new();
        // let mut actual_k_value = F::from(0);
        // equal_check.push(F::from(0));
        // k_value_proof.push(F::from(1));

        // let target = graph_triples.get(&condition[0]).unwrap().clone();
        // // This is for _attr
        // // Case 1 subject, predicate and object are considered
        // let mut target_out_degree_attr: Vec<(u64, u64)> = target
        //     .get(&condition[1])
        //     .unwrap()
        //     .clone()
        //     .iter()
        //     .filter(|vec| vec[0] == condition[0])
        //     .map(|vec| (vec[1], vec[2]))
        //     .collect();
        // // Case 2 object, only predicate is considered
        // let mut target_in_degree_attr: Vec<(u64, u64)> = target
        //     .get(&condition[1])
        //     .unwrap()
        //     .clone()
        //     .iter()
        //     .filter(|vec| vec[2] == condition[0])
        //     .map(|vec| (vec[1], vec[1]))
        //     .collect();

        // // This is for _rel
        // let mut target_inout_degree_rel: Vec<(u64, u64)> = target
        //     .get(&condition[2])
        //     .unwrap_or(&Vec::new())
        //     .clone()
        //     .iter()
        //     .map(|vec| (vec[1], vec[1]))
        //     .collect();

        // sort_vec_of_tuples(&mut target_out_degree_attr);
        // sort_vec_of_tuples(&mut target_in_degree_attr);
        // sort_vec_of_tuples(&mut target_inout_degree_rel);

        // let mut idx = 0;
        // for key in graph_triples.keys() {
        //     let o_target: HashMap<u64, Vec<Vec<u64>>> = graph_triples.get(&key).unwrap().clone();
        //     // This is for _attr
        //     // Case 1 subject, predicate and object are considered
        //     let mut o_target_out_degree_attr: Vec<(u64, u64)> = o_target
        //         .get(&condition[1])
        //         .unwrap()
        //         .clone()
        //         .iter()
        //         .filter(|vec| vec[0] == *key)
        //         .map(|vec| (vec[1], vec[2]))
        //         .collect();
        //     // Case 2 object, only predicate is considered
        //     let mut o_target_in_degree_attr: Vec<(u64, u64)> = o_target
        //         .get(&condition[1])
        //         .unwrap()
        //         .clone()
        //         .iter()
        //         .filter(|vec| vec[2] == *key)
        //         .map(|vec| (vec[1], vec[1]))
        //         .collect();
        //     // This is for _rel
        //     let mut o_target_inout_degree_rel: Vec<(u64, u64)> = o_target
        //         .get(&condition[2])
        //         .unwrap_or(&Vec::new())
        //         .clone()
        //         .iter()
        //         .map(|vec| (vec[1], vec[1]))
        //         .collect();

        //     sort_vec_of_tuples(&mut o_target_out_degree_attr);
        //     sort_vec_of_tuples(&mut o_target_in_degree_attr);
        //     sort_vec_of_tuples(&mut o_target_inout_degree_rel);

        //     let mut eq_check_value = F::from(0);
        //     let mut _k_value = F::from(1);
        //     if is_contained_tuples(&o_target_out_degree_attr, &target_out_degree_attr)
        //         && is_contained_tuples(&o_target_in_degree_attr, &target_in_degree_attr)
        //         && is_contained_tuples(&o_target_inout_degree_rel, &target_inout_degree_rel)
        //     {
        //         final_target_spo = o_target.get(&condition[1]).cloned().unwrap_or_default();
        //         final_target_spo.extend(o_target.get(&condition[2]).cloned().unwrap_or_default());
        //         eq_check_value = F::from(1);
        //         _k_value = *k_value_proof.last().unwrap() + F::from(1);
        //         actual_k_value = actual_k_value + F::from(1);
        //     }
        //     if idx > 0 {
        //         equal_check.push(eq_check_value);
        //         k_value_proof.push(_k_value);
        //     }
        //     idx = idx + 1;
        // }

        // let checked_value = if actual_k_value >= expected_k_value {
        //     F::ONE
        // } else {
        //     F::ZERO
        // };
        // println! {"Number of k-value targets: {:?}", actual_k_value};

        // let duration_block = start.elapsed();
        // println!("Time elapsed for block: {:?}", duration_block);

        layouter.assign_region(
            || "witness",
            |mut region| {
                for i in 0..graph_triples.len() {
                    self.config.q_enable[0].enable(&mut region, i)?;
                    for j in 0..graph_triples[0].len() {
                        region.assign_advice(
                            || "s",
                            self.config.graph_triples[j],
                            i,
                            || Value::known(F::from(graph_triples[i][j])),
                        )?;
                    }

                    region.assign_advice(
                        || "subject check",
                        self.config.check[0],
                        i,
                        || Value::known(s_check[i]),
                    )?;

                    region.assign_advice(
                        || "object check",
                        self.config.check[1],
                        i,
                        || Value::known(o_check[i]),
                    )?;

                    // only focus on the values after filtering
                    // if s_check[i] == F::from(1) {
                    //     self.config.q_perm[0].enable(&mut region, i)?;
                    // }

                    region.assign_advice(
                        || "subject condition",
                        self.config.subject_condition,
                        i,
                        || Value::known(F::from(condition[0])),
                    )?;
                }

                // for i in 0..final_target_spo.len() {
                //     for j in 0..final_target_spo[0].len() {
                //         region.assign_advice(
                //             || "",
                //             self.config.groupby[j],
                //             i,
                //             || Value::known(F::from(final_target_spo[i][j])),
                //         )?;
                //     }
                //     if i > 0 {
                //         self.config.q_sort[0].enable(&mut region, i)?; // groupby sort assignment
                //     }
                // }

                // for i in 0..equal_check.len() {
                //     self.config.q_accu.enable(&mut region, i)?;
                //     self.config.q_perm[1].enable(&mut region, i)?;

                //     region.assign_advice(
                //         || "equal_check",
                //         self.config.equal_check,
                //         i,
                //         || Value::known(equal_check[i]),
                //     )?;

                //     region.assign_advice(
                //         || "k_value check",
                //         self.config.kvalue_check,
                //         i,
                //         || Value::known(k_value_proof[i]),
                //     )?;
                // }

                self.config.q_enable[1].enable(&mut region, 0)?;
                region.assign_advice(
                    || "expected k value",
                    self.config.expected_k_value,
                    0,
                    || Value::known(expected_k_value),
                )?;

                // region.assign_advice(
                //     || "actual final k value",
                //     self.config.actual_k_value,
                //     0,
                //     || Value::known(actual_k_value),
                // )?;

                region.assign_advice(
                    || "threshold k value",
                    self.config.threshold_k_value,
                    0,
                    || Value::known(F::ONE),
                )?;

                // compare_chip[0].assign(&mut region, 0, &[F::ONE], &[expected_k_value])?;

                // compare_chip[1].assign(&mut region, 0, &[expected_k_value], &[actual_k_value])?;

                // region.assign_advice(
                //     || "is k value satisfied",
                //     self.config.sat_k_value,
                //     0,
                //     || Value::known(checked_value),
                // )?;

                // compare_v1_chip.assign_right_constant(
                //     &mut region,
                //     graph_triples
                //         .iter()
                //         .filter_map(|row| row.get(0)) // Get the first element of the row, if it exists
                //         .map(|&element| F::from(element)) // Convert each element to type `F`
                //         .collect(),
                //     F::from(condition[0]),
                // )?;
                for i in 0..graph_triples.len() {
                    equal_chip[0].assign(
                        &mut region,
                        i,
                        Value::known(F::from(graph_triples[i][0]) - F::from(condition[0])),
                    )?; // subject = ':1'
                    equal_chip[1].assign(
                        &mut region,
                        i,
                        Value::known(F::from(graph_triples[i][2]) - F::from(condition[0])),
                    )?; // object = ':1'
                }

                let out = region.assign_advice(
                    || "orderby",
                    self.config.instance_test,
                    0,
                    || Value::known(F::from(1)),
                )?;
                Ok(out)
            },
        )
    }

    pub fn expose_public(
        &self,
        layouter: &mut impl Layouter<F>,
        cell: AssignedCell<F, F>,
        row: usize,
    ) -> Result<(), Error> {
        layouter.constrain_instance(cell.cell(), self.config.instance, row)
    }
}

struct MyCircuit<F: Copy> {
    pub graph_triples: Vec<Vec<u64>>,
    pub condition: Vec<u64>,
    pub expected_k_value: F,

    _marker: PhantomData<F>,
}

impl<F: Copy + Default> Default for MyCircuit<F> {
    fn default() -> Self {
        Self {
            graph_triples: Vec::new(),
            condition: Default::default(),
            expected_k_value: Default::default(),
            _marker: PhantomData,
        }
    }
}

impl<F: Field + Ord> Circuit<F> for MyCircuit<F> {
    type Config = TestCircuitConfig<F>;
    type FloorPlanner = SimpleFloorPlanner;

    fn without_witnesses(&self) -> Self {
        Self::default()
    }

    fn configure(meta: &mut ConstraintSystem<F>) -> Self::Config {
        TestChip::configure(meta)
    }

    fn synthesize(
        &self,
        config: Self::Config,
        mut layouter: impl Layouter<F>,
    ) -> Result<(), Error> {
        let test_chip = TestChip::construct(config);

        let out_b_cells: AssignedCell<F, F> = test_chip.assign(
            &mut layouter,
            self.graph_triples.clone(),
            self.condition.clone(),
            self.expected_k_value.clone(),
        )?;

        test_chip.expose_public(&mut layouter, out_b_cells, 0)?;

        Ok(())
    }
}

fn generate_and_verify_proof<C: Circuit<Fp>>(
    k: u32,
    circuit: C,
    public_input: &[Fp], // Adjust the type according to your actual public input type
    proof_path: &str,
) {
    let path = get_pwd();
    println!("Pwd: {}", path);
    // Time to generate parameters
    // let params_time_start = Instant::now();
    // let params: ParamsIPA<vesta::Affine> = ParamsIPA::new(k);
    let params_path = path + "/params/param" + &k.to_string();
    // let mut fd = std::fs::File::create(&params_path).unwrap();
    // params.write(&mut fd).unwrap();
    // println!("Time to generate params {:?}", params_time_start.elapsed());

    // read params
    let mut fd = std::fs::File::open(&params_path).unwrap();
    let params = ParamsIPA::<vesta::Affine>::read(&mut fd).unwrap();

    // Time to generate verification key (vk)
    let params_time_start = Instant::now();
    let vk = keygen_vk(&params, &circuit).expect("keygen_vk should not fail");
    let params_time = params_time_start.elapsed();
    println!("Time to generate vk {:?}", params_time);

    // Time to generate proving key (pk)
    let params_time_start = Instant::now();
    let pk = keygen_pk(&params, vk.clone(), &circuit).expect("keygen_pk should not fail");
    let params_time = params_time_start.elapsed();
    println!("Time to generate pk {:?}", params_time);

    // Proof generation
    let mut rng = OsRng;
    let mut transcript = Blake2bWrite::<_, EqAffine, Challenge255<_>>::init(vec![]);
    create_proof::<IPACommitmentScheme<_>, ProverIPA<_>, _, _, _, _>(
        &params,
        &pk,
        &[circuit],
        &[&[public_input]], // Adjust as necessary for your public input handling
        &mut rng,
        &mut transcript,
    )
    .expect("proof generation should not fail");
    let proof = transcript.finalize();

    // Write proof to file
    File::create(Path::new(proof_path))
        .expect("Failed to create proof file")
        .write_all(&proof)
        .expect("Failed to write proof");
    println!("Proof written to: {}", proof_path);

    // Proof verification
    let strategy = SingleStrategy::new(&params);
    let mut transcript = Blake2bRead::<_, _, Challenge255<_>>::init(&proof[..]);
    assert!(
        verify_proof(
            &params,
            pk.get_vk(),
            strategy,
            &[&[public_input]], // Adjust as necessary
            &mut transcript
        )
        .is_ok(),
        "Proof verification failed"
    );
}

fn zkp_pkad(s: Vec<String>, c: Vec<String>) -> bool {
    let k = 10;
    let mut graph_triples: Vec<Vec<u64>> = Vec::new();
    if let Ok(triples) = create_graph(s) {
        graph_triples = triples
            .iter()
            .map(|record| {
                // println!(
                //     "{} - {} - {}",
                //     record.subject, record.predicate, record.object,
                // );
                vec![
                    string_to_u64(&record.subject),
                    string_to_u64(&record.predicate),
                    string_to_u64(&record.object),
                    // record.subject,
                    // record.predicate,
                    // record.object,
                ]
            })
            .collect();
    }

    println!("Len of graph_triples: {}\n", graph_triples.len());

    let condition = vec![
            string_to_u64(&c[0]),
        ];

    let public_input: Vec<Fp> = vec![Fp::from(1)];
    let expected_k_value = Fp::from(4);

    let circuit = MyCircuit::<Fp> {
        graph_triples,
        condition,
        expected_k_value,
        _marker: PhantomData,
    };

    // let test = true;
    let test = true;

    if test {
        let prover = MockProver::run(k, &circuit, vec![public_input]).unwrap();
        prover.assert_satisfied();
        true
    } else {
        let proof_path = get_pwd() + "/proof/proof_freebase";
        generate_and_verify_proof(k, circuit, &public_input, &proof_path);
        true
    }
}

fn main() {
    println!("------Testing dummy strings-------");
    let s: Vec<String> = vec![
        "<apple>|<banana>|<cherry>".to_string(),
        "<dog>|<cat>|<apple>".to_string(),
        "<apple>|<blue>|<green>".to_string(),
    ];
    let c: Vec<String> = vec!["<apple>".to_string()];
    println!("Testing proof: {:?}", zkp_pkad(s, c));
}
