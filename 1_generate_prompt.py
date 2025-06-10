import json
import random
import argparse
import re
from openai import OpenAI

from utils import *
from prompts import constraint_format, filter_format, input_filter, constraints_list


def shuffle_examples(constraint):
    if "Example:" not in constraint:
        return constraint

    parts = constraint.split("Example:")
    header = parts[0]
    examples = parts[1].strip().split("\n")
    random.shuffle(examples)

    shuffled_examples = "\n".join(examples)
    return f"{header}Example:\n{shuffled_examples}"


def process_data(data, proc_id, base_url, api_key, model_name):

    data = data['prompt']
    client = OpenAI(api_key=api_key, base_url=base_url)
    output0 = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": input_filter.format(data)}],
        ).choices[0].message.content
    

    # only use high quality seed data
    matches = re.findall(r"Total Score: (\d+(\.\d+)?)", output0)
    if matches:
        score = matches[-1][0]
        if float(score) < 4:
            return None
    else:
        return None

    # shuffle the constraints
    shuffled_constraints_list = [
        shuffle_examples(constraint) for constraint in constraints_list
    ]
    random.shuffle(shuffled_constraints_list)
    constraints = "\n".join(shuffled_constraints_list[:7])
    payload1_content = constraint_format.format(
        str(random.choice([2, 3, 4, 5])), constraints, data
    )

    # try 3 times
    for i in range(3):
        output1 = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": payload1_content}],
            ).choices[0].message.content
        

        output1 = output1.lstrip("\n")
        if not output1 or len(output1) < 5 or len(output1) < len(data):
            continue

        payload2_content = filter_format.format(data, output1)

        output2 = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": payload2_content}],
            ).choices[0].message.content
        

        pattern = r"\[Final Result\]:\s*(.*)"
        match = re.search(pattern, output2)

        if match:
            result = match.group(1)
            if "NO" in result:
                continue
        else:
            continue

        return {
            "original": data,
            "input_analysis": output0,
            "new": output1,
            "filter_analysis": output2,
        }

    return None


def write_jsonl_file(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        for line in data:
            f.write(json.dumps(line) + "\n")


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_file", type=str, description="The raw seed data file path"
    )
    parser.add_argument("--output_file", type=str, description="The output file path")
    parser.add_argument(
        "--num_threads",
        type=int,
        default=100,
        description="The number of threads to use",
    )
    parser.add_argument("--api_key", type=str, description="The api key for llm")
    parser.add_argument("--base_url", type=str, description="The base url for llm")
    parser.add_argument("--model_name", type=str, description="The model name for llm")

    args = parser.parse_args()
    dataset = read_jsonl_file(args.input_file)
    output_file = args.output_file

    result, length = map_with_save_and_progress(
        process_data,
        dataset,
        num_threads=args.num_threads,
        save_path=output_file,
        condition=lambda x: x is not None,
        api_key=args.api_key,
        base_url=args.base_url,
        model_name=args.model_name,
    )

    print(
        f"Results have been written to {output_file}, total number of output entries: {length}"
    )


if __name__ == "__main__":
    main()
