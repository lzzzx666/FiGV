import json
import random
import argparse
import re
from openai import OpenAI

from utils import *
from prompts import prompt_template


def process_prompt(entry, proc_id, base_url, api_key, model_name):

    new_prompt = entry.get("instruction")
    if entry.get("constraints_func") == []:
        return {
            "original": entry.get("original"),
            "instruction": new_prompt,
            "response": {},
            "constraints_func": entry.get("constraints_func"),
            "constraints_llm": entry.get("constraints_llm"),
            "type": entry.get("type"),
        }

    client = OpenAI(api_key=api_key, base_url=base_url)

    constraint_to_func = {}
    for constraint in entry.get("constraints_func"):
        func_list = []
        number_try = 0
        while len(func_list) < 3 and number_try < 5:

            number_try += 1
            response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt_template.format(constraint),
                        }
                    ],
                    timeout=300,
                ).choices[0].message.content
            

            try:
                json_dict = re.findall(r"```json(.*?)```", response, re.DOTALL)[0].strip()
            except:
                continue

            try:
                res_dict = json.loads(json_dict)
            except:
                continue

            try:
                func = res_dict["func"]
                if func is None:
                    continue
            except:
                continue

            try:
                flag = False
                for i in range(3):
                    input, output = (
                        res_dict["cases"][i]["input"],
                        res_dict["cases"][i]["output"],
                    )
                    if type(input) != str or type(output) != bool:
                        flag = True
                if flag:
                    continue
            except:
                continue

            func_list.append(res_dict)

        if func_list != []:
            constraint_to_func[constraint] = func_list

    if constraint_to_func == {}:
        return {
            "original": entry.get("original"),
            "instruction": new_prompt,
            "response": None,
            "constraints_func": entry.get("constraints_func"),
            "constraints_llm": entry.get("constraints_llm"),
            "type": entry.get("type"),
        }

    return {
        "original": entry.get("original"),
        "instruction": new_prompt,
        "response": constraint_to_func,
        "constraints_func": entry.get("constraints_func"),
        "constraints_llm": entry.get("constraints_llm"),
        "type": entry.get("type"),
    }


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
    input_file = args.input_file
    output_file = args.output_file
    data = read_jsonl_file(input_file)

    result, length = map_with_save_and_progress(
        process_prompt,
        data,
        num_threads=args.num_threads,
        save_path=output_file,
        condition=lambda x: x.get("response") is not None,
        api_key=args.api_key,
        base_url=args.base_url,
        model_name=args.model_name,
    )

    print(f"Results have been written to {output_file}, total entries: {len(length)}")


if __name__ == "__main__":
    main()
