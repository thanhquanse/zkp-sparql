use pyo3::prelude::*;

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

#[pyfunction]
fn multiply(a: i32, b: i32) -> PyResult<i32> {
    Ok(a * b)
}

#[pyfunction]
fn count_doubles(s: &str) -> PyResult<u64> {
    let mut total = 0;
    let mut chars = s.chars();
    if let Some(mut prev) = chars.next() {
        for curr in chars {
            if prev == curr {
                total += 1;
            }
            prev = curr;
        }
    }
    Ok(total)
}

#[pyfunction]
fn get_data(s: &str, c: &str) -> PyResult<bool> {
    let mut total = 0;
    let mut chars = s.chars();
    let mut ok = false;
    if let Some(mut prev) = chars.next() {
        for curr in chars {
            if prev == curr {
                total += 1;
            }
            prev = curr;
        }
    }

    if total > 0 {
        ok = true;
    }

    Ok(ok)
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
        for i in 0..self.config.equal_condition.len() {
            let chip = IsZeroChip::construct(self.config.equal_condition[i].clone());
            equal_chip.push(chip);
        }

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

                    region.assign_advice(
                        || "subject condition",
                        self.config.subject_condition,
                        i,
                        || Value::known(F::from(condition[0])),
                    )?;
                }

                self.config.q_enable[1].enable(&mut region, 0)?;
                region.assign_advice(
                    || "expected k value",
                    self.config.expected_k_value,
                    0,
                    || Value::known(expected_k_value),
                )?;

                region.assign_advice(
                    || "threshold k value",
                    self.config.threshold_k_value,
                    0,
                    || Value::known(F::ONE),
                )?;

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
    let params_time_start = Instant::now();
    let params: ParamsIPA<vesta::Affine> = ParamsIPA::new(k);
    let params_path = path + "/params/param" + &k.to_string();
    let mut fd = std::fs::File::create(&params_path).unwrap();
    params.write(&mut fd).unwrap();
    println!("Time to generate params {:?}", params_time_start.elapsed());

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

#[pyfunction]
pub fn zkp_pkad(s: Vec<String>, c: Vec<String>) -> PyResult<bool> {
    let k = 10;
    let mut graph_triples: Vec<Vec<u64>> = Vec::new();
    if let Ok(triples) = create_graph(s) {
        graph_triples = triples
            .iter()
            .map(|record| {
                vec![
                    string_to_u64(&record.subject),
                    string_to_u64(&record.predicate),
                    string_to_u64(&record.object),
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

    let test = false;

    if test {
        let prover = MockProver::run(k, &circuit, vec![public_input]).unwrap();
        prover.assert_satisfied();
    } else {
        let proof_path = get_pwd() + "/proof/proof_freebase";
        generate_and_verify_proof(k, circuit, &public_input, &proof_path);
    }
    Ok(true)
}

#[pymodule]
fn my_rust_module(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(multiply, m)?)?;
    m.add_function(wrap_pyfunction!(count_doubles, m)?)?;
    m.add_function(wrap_pyfunction!(get_data, m)?)?;
    m.add_function(wrap_pyfunction!(zkp_pkad, m)?)?;
    Ok(())
}