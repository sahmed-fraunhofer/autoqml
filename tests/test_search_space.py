from unittest import TestCase

import optuna
from optuna.samplers import TPESampler

from autoqml.search_space import Configuration
from autoqml.search_space.base import TunablePipeline
from autoqml.search_space.classification import ClassificationChoice, SVC
from autoqml.search_space.data_cleaning.imputation import (
    ConstantImputation, ImputationChoice, MeanImputation
)


class TestSearchSpace(TestCase):
    def test_single_component(self):
        constant = ConstantImputation()
        sampler = TPESampler(seed=10)
        study = optuna.create_study(sampler=sampler)
        trial = study.ask()

        cs = constant.sample_configuration(trial, {})
        self.assertListEqual(list(cs.keys()), ['constant'])

    def test_choice(self):
        choice = ImputationChoice()
        choice.trial_id = 0

        sampler = TPESampler(seed=10)
        study = optuna.create_study(sampler=sampler)
        trial = study.ask()

        cs = choice.sample_configuration(
            trial, {
                'autoqml.search_space.data_cleaning.imputation.ImputationChoice__choice':
                    'constant'
            }
        )
        self.assertEqual(set(cs.keys()), {'choice', 'constant__constant'})

        hps1: Configuration = {'choice': 'mean'}
        choice.set_params(**hps1)
        self.assertEqual(type(choice.estimator), MeanImputation)

        hps2: Configuration = {'choice': 'constant', 'constant__constant': 2}
        choice.set_params(**hps2)
        self.assertEqual(type(choice.estimator), ConstantImputation)
        # noinspection PyUnresolvedReferences
        self.assertEqual(choice.estimator.constant, 2)

    def test_pipeline_quantum(self):
        pipeline = TunablePipeline(
            steps=[
                ('imputation', ImputationChoice()
                ), ('classification', ClassificationChoice())
            ]
        )
        for _, comp in pipeline.steps:
            comp.trial_id = 0

        sampler = TPESampler(seed=10)
        study = optuna.create_study(sampler=sampler)
        trial = study.ask()

        cs = pipeline.sample_configuration(
            trial,
            {
                "autoqml.search_space.classification.ClassificationChoice__choice":
                    "qsvc"
            },
        )
        self.assertEqual(
            set(cs.keys()), {
                'imputation__choice',
                'classification__choice',
                'classification__qsvc__C',
                'classification__qsvc__num_qubits',
                'classification__qsvc__num_repetitions',
                'classification__qsvc__num_chebyshev',
                'classification__qsvc__encoding_circuit',
                'classification__qsvc__outer_kernel',
                'classification__qsvc__parameter_seed',
                'classification__qsvc__chebyshev_alpha',
                'classification__qsvc__quantum_kernel',
                'classification__qsvc__measurement',
                'classification__qsvc__trial_id',
                'imputation__constant__constant',
            }
        )

        hps: Configuration = {
            'imputation__choice': 'mean',
            'classification__choice': 'svc',
            'classification__svc__C': 1.25
        }
        pipeline.set_params(**hps)
        self.assertEqual(type(pipeline.steps[0][1].estimator), MeanImputation)
        self.assertEqual(type(pipeline.steps[1][1].estimator), SVC)
        self.assertEqual(pipeline.steps[1][1].estimator.C, 1.25)
