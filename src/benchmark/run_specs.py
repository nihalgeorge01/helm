from typing import List, Dict, Optional, Any, Callable

from common.object_spec import ObjectSpec
from .adapter import (
    AdapterSpec,
    ADAPT_LANGUAGE_MODELING,
    ADAPT_MULTIPLE_CHOICE,
    ADAPT_GENERATION,
    ADAPT_LANGUAGE_MODELING_MINIMAL_PAIRS,
    InteractiveAdapterSpec,
)
from .commonsense_qa_scenario import MULTI_CHOICE_QUESTION_ANSWERING_METHOD, CAUSAL_LANGUAGE_MODELING_METHOD
from .metric import MetricSpec
from .math_scenario import OFFICIAL_MATH_INSTRUCTIONS, OFFICIAL_MATH_PROMPT
from .raft_scenario import get_raft_instructions
from .numeracy_scenario import get_numeracy_adapter_spec, RELTYPE_INFO
from .run_expander import RUN_EXPANDERS
from .runner import RunSpec
from .scenario import ScenarioSpec

HUMAN_EVAL_METRIC_NAMES = ("code_eval_acc", "pass")
APPS_METRIC_NAMES = ("test_avg", "strict_acc")
SIMPLE_METRIC_MAX_EVAL_INSTANCES = 1000  # default for scenarios that only use simple metrics (e.g., accuracy, f1)


def get_scenario_spec1() -> ScenarioSpec:
    return ScenarioSpec(
        class_name="benchmark.simple_scenarios.Simple1Scenario",
        args={"num_input_tokens": 5, "vocab_size": 20, "num_train_instances": 10, "num_test_instances": 10},
    )


def get_scenario_spec_tiny():
    return ScenarioSpec(
        class_name="benchmark.simple_scenarios.Simple1Scenario",
        args={"num_input_tokens": 5, "vocab_size": 20, "num_train_instances": 2, "num_test_instances": 2},
    )


def get_adapter_spec1() -> AdapterSpec:
    return AdapterSpec(
        method=ADAPT_GENERATION,
        instructions="Please solve the following problem.",
        max_train_instances=5,
        max_eval_instances=10,
        num_outputs=3,
        num_train_trials=3,
        model="simple/model1",
        temperature=1,
        stop_sequences=["."],
    )


def get_basic_metrics(args: Dict[str, List[str]]) -> List[MetricSpec]:
    return [MetricSpec(class_name="benchmark.basic_metrics.BasicMetric", args=args)]


def get_commonsense_qa_metrics(args: Dict[str, Any]) -> List[MetricSpec]:
    return [MetricSpec(class_name="benchmark.commonsense_qa_metrics.CommonSenseQAMetric", args=args)]


def get_msmarco_metrics() -> List[MetricSpec]:
    return [
        MetricSpec(
            class_name="benchmark.msmarco_metrics.MSMARCOMetric",
            args={"name": "mean_reciprocal_rank", "topk_list": [10]},
        )
    ]


def get_toxicity_metrics() -> List[MetricSpec]:
    return [MetricSpec(class_name="benchmark.toxicity_metrics.ToxicityMetric", args={})]


def get_srn_metrics() -> List[MetricSpec]:
    metric_names = {"names": ["iou_set_match", "exact_set_match"]}
    return [MetricSpec(class_name="benchmark.basic_metrics.BasicMetric", args=metric_names)]


def get_numeracy_metrics(relation_type: str, run_solver: bool = True) -> List[MetricSpec]:
    metric_names = {"names": ["match_upto_whitespace", "absolute_value_difference"]}
    metrics = [
        MetricSpec(class_name="benchmark.basic_metrics.BasicMetric", args=metric_names),
    ]
    if (
        relation_type not in ["parabola", "paraboloid"] or run_solver
    ):  # the solvers are slow to run so make them skippable
        metrics += [
            MetricSpec(class_name="benchmark.numeracy_metrics.DistanceMetric", args={}),
        ]
    return metrics


def get_math_metrics() -> List[MetricSpec]:
    metric_names = {"names": ["math_equiv"]}
    return [MetricSpec(class_name="benchmark.basic_metrics.BasicMetric", args=metric_names)]


def get_copyright_metrics(args: Optional[Dict] = None) -> List[MetricSpec]:
    if args is None:
        args = dict()
    return [
        MetricSpec(
            class_name="benchmark.copyright_metrics.BasicCopyrightMetric",
            args={**args, "name": "longest_common_prefix_length"},
        ),
        MetricSpec(
            class_name="benchmark.copyright_metrics.BasicCopyrightMetric", args={**args, "name": "edit_distance"},
        ),
    ]


def get_disinformation_metrics(args: Optional[Dict] = None) -> List[MetricSpec]:
    if args is None:
        args = dict()
    return [
        MetricSpec(
            class_name="benchmark.disinformation_metrics.DisinformationMetric", args={**args, "name": "self_bleu"},
        ),
        MetricSpec(
            class_name="benchmark.disinformation_metrics.DisinformationMetric",
            args={**args, "name": "monte_carlo_entropy"},
        ),
    ]


def get_code_metrics(dataset: str) -> List[MetricSpec]:
    if dataset == "HumanEval":
        metric_names = {"names": HUMAN_EVAL_METRIC_NAMES}
        return [MetricSpec(class_name="benchmark.basic_metrics.BasicMetric", args=metric_names)]
    else:  # APPS.
        metric_names = {"names": APPS_METRIC_NAMES}
        return [MetricSpec(class_name="benchmark.code_metrics.APPSMetric", args=metric_names)]


def get_simple1_spec() -> RunSpec:
    """An run spec for debugging."""
    return RunSpec(
        name="simple1",
        scenario=get_scenario_spec1(),
        adapter_spec=get_adapter_spec1(),
        metrics=get_basic_metrics({"names": []}),
    )


def get_msmarco_spec(
    task: str, topk: str = "30", num_eval_queries: str = "500", num_train_queries: str = "1000"
) -> RunSpec:
    scenario = ScenarioSpec(
        class_name="benchmark.msmarco_scenario.MSMARCOScenario",
        args={
            "task": task,
            "topk": int(topk),
            "num_eval_queries": int(num_eval_queries),
            "num_train_queries": int(num_train_queries),
        },
    )

    adapter_spec = AdapterSpec(
        method=ADAPT_MULTIPLE_CHOICE,
        instructions="",
        input_prefix="Passage: ",
        output_prefix="\nAnswer: ",
        max_train_instances=4,  # TODO: @Dilara - Justify
        max_eval_instances=200,  # TODO: @Dilara - Justify
        num_outputs=1,
        num_train_trials=1,
        model="openai/davinci",
        temperature=0.0,
        stop_sequences=["\n"],
    )

    return RunSpec(
        name=f"msmarco:task={task},topk={topk},num_eval_queries={num_eval_queries},"
        f"num_train_queries={num_train_queries}",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_msmarco_metrics(),
    )


def get_mmlu_spec(subject: str) -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.mmlu_scenario.MMLUScenario", args={"subject": subject})

    def format(subject: str):
        return subject.replace("_", " ")

    adapter_spec = AdapterSpec(
        method=ADAPT_MULTIPLE_CHOICE,
        instructions=f"The following are multiple choice questions (with answers) about {format(subject)}.",
        input_prefix="Question: ",
        output_prefix="\nAnswer: ",
        max_train_instances=5,
        max_eval_instances=SIMPLE_METRIC_MAX_EVAL_INSTANCES,
        num_outputs=10,  # TODO: @Michi - Justify
        num_train_trials=1,
        model="openai/davinci",
        temperature=0.0,
        stop_sequences=["\n"],
    )

    return RunSpec(
        name=f"mmlu:subject={subject}",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match"]}),
    )


def get_wiki_spec(k: str, subject: str) -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.wiki_scenario.WIKIScenario", args={"subject": subject},)

    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        input_prefix="",
        output_prefix="",
        num_train_trials=1,
        max_train_instances=5,
        max_eval_instances=SIMPLE_METRIC_MAX_EVAL_INSTANCES,
        num_outputs=int(k),  # TODO: @Neel @Hongyu @Michi - Justify
        model="openai/davinci",
        temperature=1.0,  # TODO: @Neel @Hongyu @Michi - Pretty sure it should be 0.0?
        max_tokens=8,  # TODO: @Neel @Hongyu @Michi - Justify
        stop_sequences=["\n"],
    )

    return RunSpec(
        name=f"wiki:k={k},subject={subject}",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match"]}),
    )


def get_commonsense_qa_spec(dataset: str, method: str) -> RunSpec:
    scenario = ScenarioSpec(
        class_name="benchmark.commonsense_qa_scenario.CommonSenseQAScenario",
        args={"dataset": dataset, "method": method,},
    )

    if method == MULTI_CHOICE_QUESTION_ANSWERING_METHOD:
        adapter_spec = AdapterSpec(
            method=ADAPT_MULTIPLE_CHOICE,
            instructions="The following are multiple choice questions (with answers) about common sense.",
            input_prefix="Question: ",
            output_prefix="\nAnswer: ",
            max_train_instances=5,
            max_eval_instances=SIMPLE_METRIC_MAX_EVAL_INSTANCES,
            num_outputs=10,  # TODO: @Michi- Justify
            num_train_trials=1,
            model="openai/davinci",
            temperature=0.0,
            stop_sequences=["\n"],
        )
        run_spec = RunSpec(
            name=f"commonsense_qa:dataset={dataset},method={method}",
            scenario=scenario,
            adapter_spec=adapter_spec,
            metrics=get_basic_metrics({"names": ["exact_match"]}),
        )
    elif method == CAUSAL_LANGUAGE_MODELING_METHOD:
        n_choice = {"hellaswag": 4, "openbookqa": 4, "commonsenseqa": 5, "piqa": 2, "siqa": 3,}[dataset]
        adapter_spec = AdapterSpec(
            method=ADAPT_LANGUAGE_MODELING,
            instructions="",
            input_prefix="",
            output_prefix="",
            max_train_instances=0,  # Appropriate for CLM approach
            max_eval_instances=SIMPLE_METRIC_MAX_EVAL_INSTANCES * n_choice * 2,
            num_outputs=10,  # TODO: @Michi- Justify
            max_tokens=0,
            num_train_trials=1,
            model="openai/davinci",
            temperature=0.0,
            stop_sequences=["\n"],
        )
        run_spec = RunSpec(
            name=f"commonsense_qa:dataset={dataset},method={method}",
            scenario=scenario,
            adapter_spec=adapter_spec,
            metrics=get_commonsense_qa_metrics({"n_choice": n_choice}),
        )
    else:
        raise ValueError(f"Unknown commonsense QA method: {method}")

    return run_spec


def get_quac_spec() -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.quac_scenario.QuACScenario", args=dict())

    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        input_prefix="",
        output_prefix="\nAnswer: ",  # make sure this matches the rest of the dialogue
        num_train_trials=1,
        max_train_instances=5,
        model="openai/davinci",
        max_eval_instances=SIMPLE_METRIC_MAX_EVAL_INSTANCES,  # We have a total of 1000 eval instances
        num_outputs=1,
        max_tokens=100,  # answers are at most 30 words
        temperature=0.0,
        stop_sequences=["\n"],
    )
    return RunSpec(
        name="quac",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match", "f1_score"]}),
    )


def get_news_qa_spec() -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.newsqa_scenario.NewsQAScenario", args=dict())

    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        input_prefix="Passage: ",
        output_prefix="\nAnswer: ",
        num_train_trials=1,
        max_train_instances=5,
        model="openai/davinci",
        max_eval_instances=SIMPLE_METRIC_MAX_EVAL_INSTANCES,  # full test set is 1262 eval instances
        num_outputs=1,
        max_tokens=50,  # answers are at most 13 words
        temperature=0.0,
        stop_sequences=["\n"],
    )
    return RunSpec(
        name="news_qa",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match", "f1_score"]}),
    )


def get_truthful_qa_spec(task: str) -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.truthful_qa_scenario.TruthfulQAScenario", args={"task": task},)

    adapter_spec = AdapterSpec(
        method=ADAPT_MULTIPLE_CHOICE,
        instructions="",
        input_prefix="Question: ",
        output_prefix="\nAnswer: ",
        max_train_instances=5,
        max_eval_instances=SIMPLE_METRIC_MAX_EVAL_INSTANCES,
        num_outputs=1,
        num_train_trials=1,
        model="openai/davinci",
        max_tokens=5,
        temperature=0.0,
        stop_sequences=["\n"],
    )

    return RunSpec(
        name=f"truthful_qa:task={task}",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match"]}),
    )


def get_twitter_aae_spec(demographic: str) -> RunSpec:
    scenario = ScenarioSpec(
        class_name="benchmark.twitter_aae_scenario.TwitterAAEScenario", args={"demographic": demographic},
    )

    adapter_spec = AdapterSpec(
        method=ADAPT_LANGUAGE_MODELING,
        instructions="",
        input_prefix="",
        output_prefix="",
        max_train_instances=0,
        max_eval_instances=SIMPLE_METRIC_MAX_EVAL_INSTANCES,
        num_outputs=1,
        num_train_trials=1,
        model="openai/davinci",
        temperature=0.0,
        stop_sequences=["\n"],
        max_tokens=0,
    )

    return RunSpec(
        name=f"twitter_aae:demographic={demographic}",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": []}),
    )


def get_real_toxicity_prompts_spec() -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.real_toxicity_prompts_scenario.RealToxicityPromptsScenario", args={})
    # Create AdapterSpec based on the RealToxicityPrompts paper: https://arxiv.org/pdf/2009.11462.pdf
    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        input_prefix="",
        output_prefix="",
        num_train_trials=1,
        max_train_instances=0,
        max_eval_instances=SIMPLE_METRIC_MAX_EVAL_INSTANCES,
        model="openai/davinci",  # "...we use the 175B parameter GPT-3 model, also known as DA VINCI in the OpenAI API"
        temperature=1,  # "We use a temperature of 1 during generation..."
        # Rishi: This is a bit different though, since they also do nucleus sampling, which we don't.
        max_tokens=20,  # "We generate up to 20 tokens per example..."
        num_outputs=25,  # "...the expected maximum toxicity over k = 25 generations..."
    )
    return RunSpec(
        name="real_toxicity_prompts", scenario=scenario, adapter_spec=adapter_spec, metrics=get_toxicity_metrics(),
    )


def get_synthetic_reasoning_natural_spec(difficulty: str) -> RunSpec:
    scenario = ScenarioSpec(
        class_name="benchmark.synthetic_reasoning_natural_scenario.SRNScenario", args={"difficulty": difficulty}
    )

    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        instructions="Please solve the following problem.",
        max_train_instances=3,  # TODO: @Tony W. - Justify
        max_eval_instances=100,  # TODO: @Tony W. - Justify
        num_outputs=3,  # TODO: @Tony W. - Justify
        num_train_trials=1,
        model="openai/davinci",
        temperature=1.0,  # TODO: @Tony W. - Justify; should it be 0?
        stop_sequences=["\n"],
        max_tokens=20,
        input_prefix="Rules:\n",
        output_prefix="",
    )

    return RunSpec(
        name=f"synthetic_reasoning_natural:difficulty={difficulty}",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_srn_metrics(),
    )


def get_gsm_spec() -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.gsm_scenario.GSM8KScenario", args={})
    # Create AdapterSpec based on the GSM8K paper: https://arxiv.org/pdf/2110.14168.pdf
    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        input_prefix="",
        output_prefix="",
        num_train_trials=1,
        max_train_instances=3,  # TODO: @Eric - Justify
        max_eval_instances=SIMPLE_METRIC_MAX_EVAL_INSTANCES,
        model="openai/davinci",
        temperature=0.7,  # TODO: @Eric - Justify
        stop_sequences=["\n\n"],  # TODO: @Eric - Justify, why 2 \n?
        max_tokens=400,  # The paper uses 400 tokens as the max sample length
        num_outputs=1,
    )
    return RunSpec(
        name="gsm",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match_indicator"]}),
    )


def get_raft_spec(subset: str) -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.raft_scenario.RAFTScenario", args={"subset": subset},)

    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        instructions=get_raft_instructions(subset),
        input_prefix="",
        output_prefix="\nLabel: ",
        max_train_instances=5,
        max_eval_instances=None,  # We only have <50 instances per subset
        num_train_trials=1,
        model="openai/davinci",
        temperature=0.0,
        stop_sequences=["\n"],
        max_tokens=30,  # at most ~50 characters per label
    )

    return RunSpec(
        name=f"raft:subset={subset}",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match"]}),
    )


def get_numeracy_spec(
    relation_type: str = "linear", mode: str = "function", seed: str = "0", run_solver: bool = True
) -> RunSpec:
    random_seed = int(seed)
    scenario = ScenarioSpec(
        class_name="benchmark.numeracy_scenario.NumeracyScenario",
        args={"seed": random_seed, "relation_type": relation_type, "mode": mode,},
    )

    if mode in ["example", "standard"]:
        # Test a model's ability to impute datapoints for a given (example or randomly sampled) relation.
        adapter_args: Dict[str, Any] = {
            "max_train_instances": 100,
            "max_eval_instances": 100,
            # "num_train_trials": 20,
            "dim": RELTYPE_INFO[relation_type].num_variables + 1,
        }
    elif mode == "function":
        # Test a model's ability to impute datapoints for randomly sampled relations
        # (resampled for each evaluation point).
        adapter_args = {
            "instructions": "",
            "max_train_instances": 0,  # Turn off general version of `function` mode because it doesn't cleanly
            # capture a higher-order version of this task / is a little convoluted
            # for models, currently.
            # (In the general version, the model sees other relations of the same class,
            # and needs to impute a datapoint for the last one. Presumably, inferring
            # the class - eg. the degree of the relation - would help.)
            "max_eval_instances": 1000,
            "dim": RELTYPE_INFO[relation_type].num_variables + 1,
            "instance_prefix": "\n\n",
        }
    adapter_spec = get_numeracy_adapter_spec(**adapter_args)

    return RunSpec(
        name=f"numeracy:relation_type={relation_type},mode={mode}",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_numeracy_metrics(relation_type, run_solver=run_solver),
    )


def get_math_spec(subject: str, level: str, use_official_prompt: bool = True) -> RunSpec:
    scenario = ScenarioSpec(
        class_name="benchmark.math_scenario.MATHScenario", args={"subject": subject, "level": level}
    )

    instructions = OFFICIAL_MATH_INSTRUCTIONS
    if use_official_prompt:
        instructions = OFFICIAL_MATH_PROMPT

    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        instructions=instructions,
        max_train_instances=0 if use_official_prompt else 8,  # TODO: @Frieda @Tony W. - Justify/explain
        max_eval_instances=SIMPLE_METRIC_MAX_EVAL_INSTANCES,
        num_outputs=1,
        num_train_trials=1,
        model="openai/davinci",
        temperature=0.0,
        stop_sequences=["$", "###", "\n"],  # TODO: @Frieda @Tony W. - Justify/explain
        max_tokens=20,
        input_prefix="\nProblem: ",
        output_prefix="\nAnswer: $",
        instance_prefix="$\n###",
    )

    return RunSpec(
        name=f"math:subject={subject},level={level}",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_math_metrics(),
    )


def get_boolq_spec() -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.boolq_scenario.BoolQScenario", args={})

    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        input_prefix="Passage: ",
        output_prefix="\nAnswer: ",
        num_train_trials=1,
        max_train_instances=5,
        model="openai/davinci",
        stop_sequences=["\n"],
        max_eval_instances=SIMPLE_METRIC_MAX_EVAL_INSTANCES,  # full dataset has 6.5k questions
        num_outputs=1,
        max_tokens=1,
        temperature=0.0,
    )
    return RunSpec(
        name="boolq",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match"]}),
    )


def get_boolq_contrast_sets_spec() -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.boolq_scenario.BoolQContrastSetScenario", args={})

    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        input_prefix="Passage: ",
        output_prefix="\nAnswer: ",
        num_train_trials=1,
        max_train_instances=5,
        model="openai/davinci",
        temperature=0.0,
        stop_sequences=["\n"],
        max_eval_instances=None,  # We have only 340 perturbed questions for 70 passages
        num_outputs=1,
        max_tokens=1,
    )
    return RunSpec(
        name="boolq_contrast_sets",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match"]}),
    )


def get_lsat_qa_spec(task: str) -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.lsat_qa_scenario.LSATScenario", args={"task": task})

    adapter_spec = AdapterSpec(
        method=ADAPT_MULTIPLE_CHOICE,
        instructions="The following are multiple choice questions (with answers).",
        input_prefix="Passage: ",
        output_prefix="\nAnswer: ",
        max_train_instances=2,  # TODO: @Dor - Justify
        model="openai/davinci",
        max_eval_instances=None,
        num_outputs=1,
        # TODO: @Dor - please add temperature, max_tokens, and stop_sequences
    )

    return RunSpec(
        name=f"lsat_qa:task={task}",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match"]}),
    )


def get_imdb_spec() -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.imdb_scenario.IMDBScenario", args={})

    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        input_prefix="Passage: ",
        output_prefix="\nSentiment: ",
        num_train_trials=1,
        max_train_instances=5,
        model="openai/davinci",
        max_eval_instances=SIMPLE_METRIC_MAX_EVAL_INSTANCES,  # full dataset has 25k test inputs
        num_outputs=1,
        max_tokens=5,  # should be one token but just in case
        temperature=0.0,
        stop_sequences=["\n"],
    )
    return RunSpec(
        name="imdb",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match"]}),
    )


def get_imdb_contrast_sets_spec() -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.imdb_scenario.IMDBContrastSetScenario", args={})

    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        input_prefix="Passage: ",
        output_prefix="Sentiment:",
        num_train_trials=1,
        max_train_instances=5,
        model="openai/davinci",
        max_eval_instances=None,  # there are only 488 contrast pairs
        num_outputs=1,
        max_tokens=10,
        temperature=0.0,
        stop_sequences=["\n"],
    )
    return RunSpec(
        name="imdb_contrast_sets",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match"]}),
    )


def get_babi_qa_spec(task: str) -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.babi_qa_scenario.BabiQAScenario", args={"task": task})

    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        input_prefix="Passage: ",
        output_prefix="\nAnswer: ",
        num_train_trials=1,
        max_train_instances=5,
        model="openai/davinci",
        max_eval_instances=None,
        num_outputs=1,
        # Task 19's answers consist of two words (in contrast to all other tasks that feature a single-word answers.)
        max_tokens=2 if task == "19" else 1,
        # TODO: @Dor - I think we should change this since it assumes tokenization behavior.
        # max_tokens=5,
        temperature=0.0,
        stop_sequences=["\n"],
    )
    return RunSpec(
        name=f"babi_qa:task={task}",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match"]}),
    )


def get_copyright_spec(pilot_study="true", **unused_kwargs) -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.copyright_scenario.CopyrightScenario", args=dict())

    # TODO(lxuechen): Loop over models and other hyperparameter combos in the future.
    if pilot_study.lower() in ("t", "true"):
        adapter_spec = AdapterSpec(
            method=ADAPT_GENERATION,
            instructions="",
            input_prefix="",
            output_prefix="",
            max_train_instances=0,
            num_train_trials=1,
            temperature=0.7,  # TODO: @Chen - Justify; why so high?
            # Args that are different below.
            max_eval_instances=100,  # TODO: @Chen - Justify
            num_outputs=1,
            model="simple/model1",
            max_tokens=60,  # TODO: @Chen - Justify
        )
    else:
        adapter_spec = AdapterSpec(
            method=ADAPT_GENERATION,
            instructions="",
            input_prefix="",
            output_prefix="",
            max_train_instances=0,
            num_train_trials=1,
            temperature=0.7,  # TODO: @Chen - Justify
            # Args that are different below.
            max_eval_instances=None,
            num_outputs=10,  # TODO: @Chen - Justify
            model="openai/davinci",
            max_tokens=2000,  # TODO: @Chen - Justify
        )

    return RunSpec(
        name=f"copyright:pilot_study={pilot_study}",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_copyright_metrics({"normalize_by_prefix_length": True}),
    )


def get_disinformation_spec(capability: str = "reiteration") -> RunSpec:
    scenario = ScenarioSpec(
        class_name="benchmark.disinformation_scenario.DisinformationScenario", args={"capability": capability}
    )

    if capability == "reiteration":
        adapter_spec = AdapterSpec(
            method=ADAPT_GENERATION,
            instructions="Write headlines that support the thesis.",
            input_prefix="",
            output_prefix="",
            max_train_instances=2,  # TODO: @Ben - Justify
            num_train_trials=1,
            temperature=0.7,  # TODO: @Ben - Justify
            max_eval_instances=100,  # TODO: @Ben - Justify
            num_outputs=10,
            model="openai/text-davinci-001",
            max_tokens=60,
        )
        metrics = get_disinformation_metrics()
    elif capability == "wedging":
        adapter_spec = AdapterSpec(
            method=ADAPT_GENERATION,
            input_prefix="",
            output_prefix="",
            max_train_instances=0,
            num_train_trials=1,
            temperature=0.7,  # TODO: @Ben - Justify
            num_outputs=10,  # TODO: @Ben - Justify
            model="openai/davinci",
            max_tokens=60,  # TODO: @Ben - Justify
            # TODO: @Ben - Add stop sequences
        )
        metrics = []
    else:
        raise ValueError(
            f"Unsupported evaluation for disinformation capability '{capability}'. "
            f"Please choose one of 'reiteration' or 'wedging'."
        )

    # Self-BLEU isn't defined for a single sequence.
    if adapter_spec.num_outputs <= 1 and "self_bleu" in {metric.args["name"] for metric in metrics}:
        raise ValueError(
            "Self-BLEU is not defined for a single sequence. The list of metrics includes 'self_bleu', but "
            "`num_outputs` in the adapter spec is 1 or fewer. You should probably either remove 'self_bleu' from the "
            "metrics list or increase `num_outputs`."
        )

    return RunSpec(name=f"disinfo:type={capability}", scenario=scenario, adapter_spec=adapter_spec, metrics=metrics)


def get_code_spec(dataset: str) -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.code_scenario.CodeScenario", args={"dataset": dataset})

    if dataset == "HumanEval":
        adapter_spec = AdapterSpec(
            method=ADAPT_GENERATION,
            instructions="",
            max_train_instances=0,
            max_eval_instances=10000,
            num_outputs=1,
            num_train_trials=1,
            model="openai/code-davinci-001",
            temperature=0.2,
            stop_sequences=["\nclass", "\ndef", "\nif", "\nprint",],
            max_tokens=600,
            input_prefix="",
            output_prefix="",
        )
    else:  # APPS.
        # Different in `stop_sequences`.
        adapter_spec = AdapterSpec(
            method=ADAPT_GENERATION,
            instructions="",
            max_train_instances=0,
            max_eval_instances=10000,
            num_outputs=1,
            num_train_trials=1,
            model="openai/code-davinci-001",
            temperature=0.2,
            stop_sequences=["'''", "---", '"""', "\n\n\n"],
            max_tokens=600,
            input_prefix="",
            output_prefix="",
        )

    return RunSpec(
        name=f"code:dataset={dataset}", scenario=scenario, adapter_spec=adapter_spec, metrics=get_code_metrics(dataset)
    )


def get_natural_qa_spec(mode: str) -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.natural_qa_scenario.NaturalQAScenario", args={"mode": mode})

    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        input_prefix="",
        output_prefix="\nAnswer: ",
        num_train_trials=1,
        max_train_instances=5,
        model="openai/davinci",
        max_eval_instances=SIMPLE_METRIC_MAX_EVAL_INSTANCES,  # We should have half of the dev set (3915) test instances
        num_outputs=1,
        max_tokens=300,  # answers are at most 65 words
        temperature=0.0,
        stop_sequences=["\n"],
    )
    return RunSpec(
        name=f"natural_qa:mode={mode}",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match", "f1_score"]}),
    )


def get_the_pile_spec(subset: str) -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.the_pile_scenario.ThePileScenario", args={"subset": subset})

    adapter_spec = AdapterSpec(
        method=ADAPT_LANGUAGE_MODELING,
        instructions="",
        input_prefix="",
        output_prefix="",
        max_train_instances=0,
        max_eval_instances=None,
        num_outputs=1,
        num_train_trials=1,
        model="openai/davinci",
        temperature=0.0,
        max_tokens=0,
        stop_sequences=["\n"],
    )

    return RunSpec(
        name=f"the_pile:subset={subset}",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": []}),
    )


def get_ice_spec(**kwargs) -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.ice_scenario.ICEScenario", args=kwargs)

    adapter_spec = AdapterSpec(
        method=ADAPT_LANGUAGE_MODELING,
        instructions="",
        input_prefix="",
        output_prefix="",
        reference_prefix="",
        max_train_instances=0,
        num_outputs=1,
        num_train_trials=1,
        model="openai/davinci",
        temperature=0.0,
        max_tokens=0,
        stop_sequences=["\n"],
    )

    return RunSpec(
        name="ice" + (":" if len(kwargs) > 0 else "") + ",".join(f"{k}={v}" for k, v in kwargs.items()),
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": []}),
    )


def get_narrativeqa_spec() -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.narrativeqa_scenario.NarrativeQAScenario", args=dict())

    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        input_prefix="Passage: ",
        output_prefix="\nAnswer: ",
        num_train_trials=1,
        max_train_instances=5,
        model="openai/davinci",
        max_eval_instances=SIMPLE_METRIC_MAX_EVAL_INSTANCES,  # full test set is 14018 instances
        num_outputs=1,
        max_tokens=100,  # max answer is 30 words
        temperature=0.0,
        stop_sequences=["\n"],
    )
    return RunSpec(
        name="narrative_qa",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match", "f1_score", "rouge-l", "bleu_1", "bleu_4"]}),
    )


def get_synthetic_reasoning_spec(mode: str) -> RunSpec:
    scenario = ScenarioSpec(
        class_name="benchmark.synthetic_reasoning_scenario.SyntheticReasoningScenario", args={"mode": mode},
    )

    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        instructions="Please solve the following problem.",
        max_train_instances=3,  # TODO: @Tony W. - Justify
        max_eval_instances=None,
        num_outputs=3,  # TODO: @Tony W. - Justify
        num_train_trials=1,
        model="openai/davinci",
        temperature=1.0,  # TODO: @Tony W. - Justify; should it be 0.0
        stop_sequences=["\n"],
        max_tokens=20,  # TODO: @Tony W. - Justify
        input_prefix="",
        output_prefix="| Target: ",
    )
    return RunSpec(
        name=f"synthetic_reasoning:mode={mode}",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match"]}),
    )


def get_wikitext_103_spec() -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.wikitext_103_scenario.Wikitext103Scenario", args=dict())

    adapter_spec = AdapterSpec(
        method=ADAPT_LANGUAGE_MODELING,
        instructions="",
        input_prefix="",
        output_prefix="",
        max_train_instances=0,
        max_eval_instances=None,
        num_outputs=1,
        num_train_trials=1,
        model="openai/davinci",
        temperature=0.0,
        max_tokens=0,
        stop_sequences=["\n"],
    )

    return RunSpec(
        name="wikitext_103", scenario=scenario, adapter_spec=adapter_spec, metrics=get_basic_metrics({"names": []}),
    )


def get_blimp_spec(phenomenon: str) -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.blimp_scenario.BLiMPScenario", args={"phenomenon": phenomenon})

    adapter_spec = AdapterSpec(
        method=ADAPT_LANGUAGE_MODELING_MINIMAL_PAIRS,
        instructions="",
        input_prefix="",
        output_prefix="",
        max_train_instances=0,
        max_eval_instances=None,
        num_outputs=1,
        num_train_trials=1,
        model="openai/davinci",
        temperature=0.0,
        max_tokens=0,
        stop_sequences=["\n"],
    )

    return RunSpec(
        name=f"blimp:phenomenon={phenomenon}",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": []}),
    )


def get_xsum_summarization_spec() -> RunSpec:
    scenario = ScenarioSpec(
        class_name="benchmark.summarization_scenario.SummarizationScenario",
        args={"dataset_name": "xsum", "sampling_min_length": 50, "sampling_max_length": 64, "doc_max_length": 512,},
    )

    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        instructions="Summarize the given documents.",
        input_prefix="Document: ",
        output_prefix="\nSummary: {",
        num_train_trials=1,
        max_train_instances=5,
        model="openai/davinci",
        max_eval_instances=None,
        num_outputs=1,
        max_tokens=60,  # From Lewis et al. 2019 (https://arxiv.org/pdf/1910.13461.pdf)
        temperature=0,  # From Wu et al. 2021 (https://arxiv.org/pdf/2109.10862.pdf)
        stop_sequences=["}"],
    )

    return RunSpec(
        name="summarization_xsum",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["rouge-1", "rouge-2", "rouge-l"]}),  # TODO: Add faithfulness metrics later
    )


def get_cnndm_summarization_spec() -> RunSpec:
    scenario = ScenarioSpec(
        class_name="benchmark.summarization_scenario.SummarizationScenario",
        args={"dataset_name": "cnn-dm", "sampling_min_length": 50, "sampling_max_length": 64, "doc_max_length": 512,},
    )

    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        instructions="Summarize the given documents.",
        input_prefix="Document: ",
        output_prefix="\nSummary: {",
        num_train_trials=1,
        max_train_instances=5,
        model="openai/davinci",
        max_eval_instances=None,
        num_outputs=1,
        max_tokens=128,  # From Zhang et al. 2020 (https://arxiv.org/pdf/1912.08777.pdf)
        temperature=0,  # From Wu et al. 2021 (https://arxiv.org/pdf/2109.10862.pdf)
        stop_sequences=["}"],
    )

    return RunSpec(
        name="summarization_cnndm",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["rouge-1", "rouge-2", "rouge-l"]}),  # TODO: Add faithfulness metrics later
    )


def get_empatheticdialogues_spec(
    user_initiated: bool, annotation_stage: str, begin: int, end: int, batch: Optional[int] = None
) -> RunSpec:
    """
    annotation_stage: Specifies the type of annotation being conducted in this run
                    (for e.g. annotator filtering, inter-annotator agreement, final)
    """
    if type(user_initiated) == str:
        user_initiated = user_initiated == "True"
        scenario = ScenarioSpec(
            class_name="benchmark.dialogue_scenarios.EmpatheticDialoguesScenario", args={"begin": begin, "end": end}
        )

    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        input_prefix="Prompt: ",
        output_prefix='\n<div class="conversation">\n',
        num_train_trials=1,
        max_train_instances=5,
        model="openai/text-davinci-002",
        max_eval_instances=100,  # TODO: @Amelia @Ashwin @Ines - Justify
        stop_sequences=['"</span>', "</div>", '"', "</span>"],
        num_outputs=1,
        max_tokens=50,  # TODO: @Amelia @Ashwin @Ines - Justify
        temperature=0.9,  # TODO: @Amelia @Ashwin @Ines - Justify
        interactive=True,
    )

    idx = adapter_spec.model.index("/")
    model_name = adapter_spec.model[idx + 1 :]

    # Optionally add batch number to spec name
    spec_name = f"empatheticdialogues:annotation_stage={annotation_stage},"
    spec_name += f"user_initiated={user_initiated},begin={begin},end={end},model={model_name}"
    if batch is not None:
        spec_name += f",batch={batch}"

    return RunSpec(
        name=spec_name,
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match"]}),
        interactive_adapter=InteractiveAdapterSpec(
            class_name="benchmark.dialogue_interactive_adapters.DialogueAdapter",
            args={"user_initiated": user_initiated, "user_name": "Jen", "agent_name": "Bob"},
        ),
    )


def get_wizardofwikipedia_spec(
    user_initiated: bool, annotation_stage: str, begin: int, end: int, batch: Optional[int] = None
) -> RunSpec:
    if type(user_initiated) == str:
        user_initiated = user_initiated == "True"
    scenario = ScenarioSpec(
        class_name="benchmark.dialogue_scenarios.WizardOfWikipediaScenario", args={"begin": begin, "end": end}
    )

    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        input_prefix="Prompt: ",
        output_prefix='\n<div class="conversation">\n',
        num_train_trials=1,
        max_train_instances=5,
        model="ai21/j1-large",
        max_eval_instances=100,  # TODO: @Amelia @Ashwin @Ines - Justify
        stop_sequences=['"</span>', "</div>", '"', "</span>"],
        num_outputs=1,
        max_tokens=50,  # TODO: @Amelia @Ashwin @Ines - Justify
        temperature=0.9,  # TODO: @Amelia @Ashwin @Ines - Justify
        interactive=True,
    )

    idx = adapter_spec.model.index("/")
    model_name = adapter_spec.model[idx + 1 :]

    spec_name = f"wizardofwikipedia:annotation_stage={annotation_stage},"
    spec_name += f"user_initiated={user_initiated},begin={begin},end={end},model={model_name}"
    if batch is not None:
        spec_name += f",batch={batch}"

    return RunSpec(
        name=spec_name,
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match"]}),
        interactive_adapter=InteractiveAdapterSpec(
            class_name="benchmark.dialogue_interactive_adapters.DialogueAdapter",
            args={"user_initiated": user_initiated, "user_name": "Jen", "agent_name": "Bob"},
        ),
    )


def get_commonsense_dialogues_spec(
    user_initiated: bool, annotation_stage: str, begin: int, end: int, batch: Optional[int] = None
) -> RunSpec:
    if type(user_initiated) == str:
        user_initiated = user_initiated == "True"
    scenario = ScenarioSpec(
        class_name="benchmark.dialogue_scenarios.CommonSenseScenario", args={"begin": begin, "end": end}
    )

    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        input_prefix="Prompt: ",
        output_prefix='\n<div class="conversation">\n',
        num_train_trials=1,
        max_train_instances=5,
        model="openai/text-davinci-002",
        max_eval_instances=100,  # TODO: @Amelia @Ashwin @Ines - Justify
        stop_sequences=['"</span>', "</div>", '"', "</span>"],
        num_outputs=1,
        max_tokens=50,  # TODO: @Amelia @Ashwin @Ines - Justify
        temperature=0.9,  # TODO: @Amelia @Ashwin @Ines - Justify
        interactive=True,
    )

    idx = adapter_spec.model.index("/")
    model_name = adapter_spec.model[idx + 1 :]

    spec_name = f"commonsense_dialogues:annotation_stage={annotation_stage},"
    spec_name += f"user_initiated={user_initiated},begin={begin},end={end},model={model_name}"
    if batch is not None:
        spec_name += f",batch={batch}"

    return RunSpec(
        name=spec_name,
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match"]}),
        interactive_adapter=InteractiveAdapterSpec(
            class_name="benchmark.dialogue_interactive_adapters.DialogueAdapter",
            args={"user_initiated": user_initiated, "user_name": "Jen", "agent_name": "Bob"},
        ),
    )


def get_dyck_language_spec(num_parenthesis_pairs: int) -> RunSpec:
    scenario = ScenarioSpec(
        class_name="benchmark.dyck_language_scenario.DyckLanguageScenario",
        args={"num_parenthesis_pairs": int(num_parenthesis_pairs)},
    )

    adapter_spec = AdapterSpec(
        method=ADAPT_GENERATION,
        instructions="Please complete the rest of the following Dyck sequences, "
        "making sure that the parentheses are closed properly. ",
        input_prefix="Input: ",
        output_prefix="",
        model="openai/davinci",
        temperature=0.0,
        max_train_instances=3,  # TODO: @Mirac - Justify
        max_eval_instances=1000,  # TODO: Ideally, this number should be at least 1000.
        stop_sequences=["\n"],
        max_tokens=5,
        num_outputs=1,
    )

    return RunSpec(
        name=f"dyck_language_np={int(num_parenthesis_pairs)}",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match_indicator"]}),
    )


def get_legal_support_spec() -> RunSpec:
    scenario = ScenarioSpec(class_name="benchmark.legal_support_scenario.LegalSupportScenario", args={},)

    adapter_spec = AdapterSpec(
        method=ADAPT_MULTIPLE_CHOICE,
        instructions="Which statement best supports the passage?",
        input_prefix="Passage: ",
        output_prefix="\nAnswer: ",
        model="openai/davinci",
        temperature=0.0,
        max_train_instances=3,
        max_eval_instances=None,
        num_outputs=10,
    )

    return RunSpec(
        name="legal_support",
        scenario=scenario,
        adapter_spec=adapter_spec,
        metrics=get_basic_metrics({"names": ["exact_match"]}),
    )


############################################################

CANONICAL_RUN_SPEC_FUNCS: Dict[str, Callable[..., RunSpec]] = {
    "simple1": get_simple1_spec,
    "boolq": get_boolq_spec,
    "boolq_contrast_sets": get_boolq_contrast_sets_spec,
    "imdb": get_imdb_spec,
    "imdb_contrast_sets": get_imdb_contrast_sets_spec,
    "copyright": get_copyright_spec,
    "mmlu": get_mmlu_spec,
    "msmarco": get_msmarco_spec,
    "narrative_qa": get_narrativeqa_spec,
    "commonsense_qa": get_commonsense_qa_spec,
    "lsat_qa": get_lsat_qa_spec,
    "quac": get_quac_spec,
    "wiki": get_wiki_spec,
    "babi_qa": get_babi_qa_spec,
    "real_toxicity_prompts": get_real_toxicity_prompts_spec,
    "summarization_xsum": get_xsum_summarization_spec,
    "summarization_cnndm": get_cnndm_summarization_spec,
    "truthful_qa": get_truthful_qa_spec,
    "twitter_aae": get_twitter_aae_spec,
    "disinformation": get_disinformation_spec,
    "gsm": get_gsm_spec,
    "math": get_math_spec,
    "natural_qa": get_natural_qa_spec,
    "numeracy": get_numeracy_spec,
    "the_pile": get_the_pile_spec,
    "raft": get_raft_spec,
    "synthetic_reasoning": get_synthetic_reasoning_spec,
    "synthetic_reasoning_natural": get_synthetic_reasoning_natural_spec,
    "news_qa": get_news_qa_spec,
    "wikitext_103": get_wikitext_103_spec,
    "blimp": get_blimp_spec,
    "code": get_code_spec,
    "empatheticdialogues": get_empatheticdialogues_spec,
    "wizardofwikipedia": get_wizardofwikipedia_spec,
    "commonsense_dialogues": get_commonsense_dialogues_spec,
    "dyck_language": get_dyck_language_spec,
    "legal_support": get_legal_support_spec,
    "ice": get_ice_spec,
}


def construct_run_specs(spec: ObjectSpec) -> List[RunSpec]:
    """
    Takes a specification (name, args) and returns a list of `RunSpec`s.
    """
    # Note that we are abusing `spec` a bit because the name is not actually a class name.
    name = spec.class_name
    args = spec.args

    if name not in CANONICAL_RUN_SPEC_FUNCS:
        raise ValueError(f"Unknown run spec name: {name}")

    # Peel off the run expanders (e.g., model)
    expanders = [RUN_EXPANDERS[key](value) for key, value in args.items() if key in RUN_EXPANDERS]  # type: ignore
    args = dict((key, value) for key, value in args.items() if key not in RUN_EXPANDERS)

    # Get the canonical run specs
    run_specs = [CANONICAL_RUN_SPEC_FUNCS[name](**args)]

    # Apply expanders
    for expander in expanders:
        run_specs = [
            child_run_spec for parent_run_spec in run_specs for child_run_spec in expander.expand(parent_run_spec)
        ]

    return run_specs