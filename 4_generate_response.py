import json
import random
import argparse
import re
import os
from openai import OpenAI

from verification_function_lib import *
from prompts import follow_judger
from utils import *


def process_prompt(entry, proc_id, base_url, api_key, model_name, threshold):
    original_prompt = entry.get("original")
    instruction = entry.get("instruction")
    constraints_2_func = entry.get("constraints_2_func")
    constraints_func = entry.get("constraints_func")
    constraints_llm = entry.get("constraints_llm")
    type = entry.get("type")

    best_follow_rate = 0.0
    best_answer = None

    client = OpenAI(api_key=api_key, base_url=base_url)

    for _ in range(3):
        
        response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": instruction}],
                temperature=0.7,
                max_tokens=4096,
            ).choices[0].message.content
        
        response = response.lstrip("\n")

        follow_list1 = [0 for _ in range(len(constraints_func) + len(constraints_llm))]
        if constraints_2_func is not None and len(constraints_2_func) > 0:
            for i, constraint in enumerate(constraints_2_func.keys()):
                for func in constraints_2_func[constraint]["eval_funcs"]:
                    results = []
                    code_str = func[0]
                    local_vars = {}
                    exec(code_str, globals(), local_vars)
                    try:
                        evaluate = local_vars["evaluate"]
                        result = evaluate(response)
                        results.append(result)
                    except:
                        continue

                if len(results) == 0:
                    continue
                if not isinstance(results[0], bool):
                    continue

                follow_list1[i] += 0.5 * sum(results) / len(results)

        for i in range(3):
            if flag:
                break
            follow = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "user",
                            "content": follow_judger.format(
                                entry["instruction"],
                                response,
                                str(
                                    entry["constraints_func"] + entry["constraints_llm"]
                                ),
                            ),
                        }
                    ],
                    temperature=0.7,
                    max_tokens=4096,
                ).choices[0].message.content
            

            follow = follow.lstrip("\n")
            try:
                follow_json = re.findall(r"```json(.*?)```", follow, re.DOTALL)[
                    0
                ].strip()
                follow_json = json.loads(follow_json)
                follow_list = follow_json["Final_result"]
                if not isinstance(follow_list, list):
                    continue
                if not isinstance(follow_list[0], bool):
                    continue

                if len(follow_list) != len(constraints_func) + len(constraints_llm):
                    continue

                flag = True
                for i, follow in enumerate(follow_list):
                    if i >= len(constraints_func):
                        follow_list1[i] += follow
                    else:
                        follow_list1[i] += 0.5 * follow

            except:
                continue

        if flag == False:
            continue

        follow_rate = sum(follow_list1) / len(follow_list1)
        if follow_rate > best_follow_rate:
            best_follow_rate = follow_rate
            best_answer = response

    if best_answer is not None and best_follow_rate > threshold:
        return {
            "original": original_prompt,
            "prompt": instruction,
            "response": best_answer,
            "type": type,
            "rate": best_follow_rate,
        }

    return {
        "original": original_prompt,
        "prompt": instruction,
        "response": None,
        "type": type,
        "rate": None,
    }


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_file",
        type=str,
        description="The data file with augmented prompts and their constraints and verification functions",
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
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        description="The threshold for the follow rate",
    )

    args = parser.parse_args()
    data = read_jsonl_file(args.input_file)
    output_file = args.output_file

    result, length = map_with_save_and_progress(
        process_prompt,
        data,
        num_threads=args.num_threads,
        save_path=output_file,
        condition=lambda x: x.get("response") is not None,
        api_key=args.api_key,
        base_url=args.base_url,
        model_name=args.model_name,
        threshold=args.threshold,
    )

    print(
        f"Results have been written to {output_file}, total number of output entries: {length}"
    )


if __name__ == "__main__":
    main()
