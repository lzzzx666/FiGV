import json
import random
import argparse
import re
import os
from openai import OpenAI

from verification_function_lib import *
from prompts import follow_judger
from utils import *


def process_prompt(entry, proc_id, base_url, api_key, model_name, threshold, diff_threshold):

    client = OpenAI(api_key=api_key, base_url=base_url)

    original_prompt = entry.get("original")
    instruction = entry.get("instruction")
    constraints_2_func = entry.get("constraints_2_func")
    constraints_func = entry.get("constraints_func")
    constraints_llm = entry.get("constraints_llm")

    response_list = []
    score_list = []

    for _ in range(8):

        response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": instruction}],
                temperature=0.8,
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

                follow_list1[i] += 0.5 * sum(results) / len(results)

        content = follow_judger.format(
            entry["instruction"],
            response,
            str(entry["constraints_func"] + entry["constraints_llm"]),
        )

        flag = False

        for i in range(3):
            
            if flag:
                break
            follow = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": content}],
                    temperature=0.7,
                    max_tokens=4096,
                ).choices[0].message.content
            
            try:
                follow_json = re.findall(r"```json(.*?)```", follow, re.DOTALL)[0].strip()
                follow_json = json.loads(follow_json)
                follow_list = follow_json["Final_result"]
                if not isinstance(follow_list, list):
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
        score_list.append(follow_rate), response_list.append(response)

    if len(score_list) < 3:
        return {
            "original": original_prompt,
            "prompt": instruction,
            "chosen": None,
            "reject": None,
            "chosen_rate": None,
            "reject_rate": None,
            "type": type,
        }

    paired = list(zip(score_list, response_list))
    sorted_paired = sorted(paired, key=lambda x: x[0], reverse=True)
    sorted_score, sorted_response = zip(*sorted_paired)
    chosen = sorted_response[0]
    reject = sorted_response[-1]
    chosen_rate = sorted_score[0]
    reject_rate = sorted_score[-1]

    if chosen_rate > threshold and chosen_rate - reject_rate > diff_threshold:
        return {
            "original": original_prompt,
            "prompt": instruction,
            "chosen": chosen,
            "reject": reject,
            "chosen_rate": chosen_rate,
            "reject_rate": reject_rate,
            "type": type,
        }

    return {
        "original": original_prompt,
        "prompt": instruction,
        "chosen": None,
        "reject": None,
        "chosen_rate": None,
        "reject_rate": None,
        "type": type,
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
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.75,
        description="The threshold for the follow rate of chosen response",
    )
    parser.add_argument(
        "--diff_threshold",
        type=float,
        default=0.7,
        description="The threshold for the follow rate difference between chosen and reject response",
    )
    

    args = parser.parse_args()
    data = read_jsonl_file(args.input_file)
    output_file = args.output_file

    result, length = map_with_save_and_progress(
        process_prompt,
        data,
        num_threads=args.num_threads,
        save_path=output_file,
        condition=lambda x: x.get("chosen") is not None,
        api_key=args.api_key,
        base_url=args.base_url,
        model_name=args.model_name,
        threshold=args.threshold,
        diff_threshold=args.diff_threshold,
    )

    print(
        f"Results have been written to {output_file}, total number of output entries: {length}"
    )


if __name__ == "__main__":
    main()
