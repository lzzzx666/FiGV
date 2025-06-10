import json
import random
import argparse
import re
from openai import OpenAI

from prompts import constraints_extractor
from utils import *


def process_prompt(entry, proc_id, base_url, api_key, model_name):

    original_prompt = entry.get("original")
    new_prompt = entry.get("new")

    client = OpenAI(api_key=api_key, base_url=base_url)

    for i in range(5):
        response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": constraints_extractor.format(
                            original_instruction=original_prompt,
                            revised_instruction=new_prompt,
                        ),
                    }
                ],
                temperature=0.7,
                max_tokens=4096,
            ).choices[0].message.content
        
        try:
            json_dict = re.findall(r"```json(.*?)```", response, re.DOTALL)[0].strip()
        except:
            continue
        try:
            json.dumps(json_dict)
            res_dict = json.loads(json_dict.replace("\\", "\\\\"))
        except:
            continue
        try:
            constraints_dict = res_dict["Constraints_extracted"]
            final_result = res_dict["Final_result"]
        except:
            continue

        if len(constraints_dict) == 0 or len(final_result) == 0:
            continue

        constraints_func = []
        constraints_llm = []

        for k, v in constraints_dict.items():
            if k in final_result:
                constraints_func.append(v)
            else:
                constraints_llm.append(v)

        if len(constraints_func) + len(constraints_llm) != len(constraints_dict):
            continue

        return {
            "original": entry.get("original"),
            "instruction": new_prompt,
            "constraints_func": constraints_func,
            "constraints_llm": constraints_llm,
            "type": entry.get("type"),
        }

    print("failed to find FINAL RESULT")
    return {
        "original": entry.get("original"),
        "instruction": new_prompt,
        "constraints_func": None,
        "constraints_llm": None,
        "type": entry.get("type"),
    }


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_file", type=str, description="The data path of augmented prompts"
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
    data = read_jsonl_file(args.input_file)
    output_file = args.output_file

    result, length = map_with_save_and_progress(
        process_prompt,
        data,
        num_threads=args.num_threads,
        save_path=output_file,
        condition=lambda x: x.get("constraints_func") is not None,
        api_key=args.api_key,
        base_url=args.base_url,
        model_name=args.model_name,
    )

    print(
        f"Results have been written to {output_file}, total number of output entries: {length}"
    )


if __name__ == "__main__":
    main()
