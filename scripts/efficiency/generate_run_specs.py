"""
This script generates run_specs for the synthetic_efficiency_scenario.
"""


import argparse
from datetime import datetime


def generate_spec(scenario, model, tokenizer, num_prompt_tokens, num_output_tokens, random):
    random_str: str = ""
    if random is not None:
        random_str = f",random={random}"
    return (
        f'"{scenario}:model={model},tokenizer={tokenizer},'
        f"num_prompt_tokens={num_prompt_tokens},"
        f"num_output_tokens={num_output_tokens},"
        f"num_train_trials=default"
        f'{random_str}": '
        "{priority: 1}"
    )


def main(args):
    now = datetime.now()
    current_date = now.strftime("%m/%d/%Y")

    all_num_prompt_tokens = [1, 256, 512, 1024, 1536]
    all_num_output_tokens = [1, 2, 4, 8, 16, 32, 64]

    scenario = "synthetic_efficiency"
    if args.tokenizer_provider == "ai21":
        all_models_and_tokenizers = [("ai21_tokenizer", "ai21/j1")]
    elif args.tokenizer_provider == "openai":
        all_models_and_tokenizers = [("gpt2_tokenizer", "huggingface/gpt2")]
    elif args.tokenizer_provider == "cohere":
        all_models_and_tokenizers = [("cohere_tokenizer", "cohere/cohere")]
    elif args.tokenizer_provider == "opt":
        all_models_and_tokenizers = [("opt_tokenizer", "meta/opt")]
    elif args.tokenizer_provider == "yandex":
        all_models_and_tokenizers = [("together/yalm", "yandex/yalm")]

    specs = []

    num_specs = len(all_models_and_tokenizers) * len(all_num_prompt_tokens) * len(all_num_output_tokens)
    print(f"Generating {num_specs} specs...")

    for model, tokenizer in all_models_and_tokenizers:
        for num_prompt_tokens in all_num_prompt_tokens:
            for num_output_tokens in all_num_output_tokens:
                if args.no_random:
                    random = None
                else:
                    random = current_date
                spec = generate_spec(scenario, model, tokenizer, num_prompt_tokens, num_output_tokens, random=random)
                specs.append(spec)

    print(f"Writing out {len(specs)} specs...")
    with open(args.output_path, "w") as f:
        for spec in specs:
            f.write(f"{spec}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tokenizer_provider", choices=["ai21", "openai", "cohere", "opt", "yandex"], required=True)
    parser.add_argument("--output_path", required=True, type=str)
    parser.add_argument("--no-random", action="store_true")
    args = parser.parse_args()
    main(args)
