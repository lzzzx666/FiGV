import jsonlines
import json
import numpy as np
import logging
import signal
import warnings
import argparse
from tqdm import tqdm


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_file",
        type=str,
        description="The data file with functions we want to cross validate",
    )
    parser.add_argument("--output_file", type=str, description="The output file path")

    args = parser.parse_args()
    path = args.input_file

    with jsonlines.open(path) as reader:
        results = list(reader)

    warnings.simplefilter("error", Warning)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    logging.info("Preprocess verification functions")

    collect_packages = []
    for i, result in enumerate(results):
        if result["response"] is None:
            continue
        res = result["response"]
        for value in res.values():
            for pair in value:
                func = pair["func"]
                if "\\n" in func:
                    func = func.replace("\\n", "\n")
                try:
                    exec(func)
                except Exception as e:
                    logging.error(f"Error executing function: {e}")
                    continue
                except:
                    continue

                for line in func.split("\n"):
                    if "import" in line or "download" in line or "requests" in line:
                        collect_packages.append(line)

    with open("packages.txt", "w") as f:
        for each in list(set(collect_packages)):
            f.write(each + "\n")

    logging.info("-----------------" * 4)
    # You can break here and put the module your verification functions depend on in the verification_function_lib.py

    def convert_str(s):
        if s.lower() == "true":
            return True
        return False

    logging.info("Cross validation for functions and cases")

    def timeout_handler(signum, frame):
        raise TimeoutError("Function execution timed out")

    def evaluate_function(func, test_cases):
        local_vars = {}
        try:
            exec(func, globals(), local_vars)
            if "evaluate" not in local_vars:
                return None, "No evaluate function found"
            eval_func = local_vars["evaluate"]
        except Exception as e:
            return None, f"Error executing function: {e}"
        except:
            return None, f"Error executing function: {e}"

        acc = []
        for inp, out in test_cases:
            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(1)
                res = eval_func(inp)
            except Exception as e:
                res = None
                logging.error(f"Error during evaluation: {e}")
            except:
                res = None
            finally:
                signal.alarm(0)
            try:
                if (
                    res is None
                    or (type(out) == bool and res != out)
                    or (type(out) == str and res != convert_str(out))
                ):
                    acc.append(0)
                else:
                    acc.append(1)
            except:
                acc.append(0)

        return np.mean(acc) if acc else 0, None

    with jsonlines.open(args.output_file, "a") as f:
        for result in tqdm(results):
            if result["response"] is {}:
                f.write(
                    {
                        "original": result["original"],
                        "instruction": result["instruction"],
                        "constraints_2_func": {},
                        "constraints_func": result["constraints_func"],
                        "constraints_llm": result["constraints_llm"],
                        "type": result["type"],
                    }
                )
                continue

            res = result["response"]
            constraints_func = {}
            for constraint, value in res.items():
                eval_funcs, test_cases = [], []
                for pair in value:
                    func = pair["func"]

                    try:
                        func = func.strip()
                        func = "\n".join(
                            [
                                each
                                for each in func.split("\n")
                                if "download" not in each and "requests" not in each
                            ]
                        )
                    except Exception as e:
                        logging.error(f"Error processing function: {e}")
                        continue
                    except:
                        continue
                    try:
                        exec(func)
                    except Exception as e:
                        logging.error(f"Error executing function: {e}")
                        continue
                    except:
                        continue
                    if "transformers" in func or "huggingface" in func:
                        continue
                    eval_funcs.append(func)
                    for each in pair["cases"]:
                        test_cases.append((each["input"], each["output"]))

                eval_funcs = list(set(eval_funcs))
                if any("path/to" in string for string in eval_funcs):
                    continue
                test_cases = list(map(json.loads, set(map(json.dumps, test_cases))))

                if len(eval_funcs) < 1 or len(test_cases) < 3:
                    continue

                filtered_test_cases = []
                for each in test_cases:
                    flag = False
                    for func in eval_funcs:
                        acc, error = evaluate_function(func, [each])
                        if error:
                            logging.error(error)
                            continue
                        if acc > 0:
                            flag = True
                            break
                    if flag:
                        filtered_test_cases.append(each)

                if len(filtered_test_cases) == 0:
                    continue

                scored_funcs = []
                for func in eval_funcs:
                    acc, error = evaluate_function(func, filtered_test_cases)
                    if error:
                        logging.error(error)
                        continue
                    scored_funcs.append((func, acc))

                valid_funcs = [each for each in scored_funcs if each[1] >= 0.75]

                if not valid_funcs:
                    continue

                constraints_func[constraint] = {
                    "eval_funcs": valid_funcs,
                    "test_cases": filtered_test_cases,
                }

            f.write(
                {
                    "original": result["original"],
                    "instruction": result["instruction"],
                    "constraints_2_func": constraints_func,
                    "constraints_func": result["constraints_func"],
                    "constraints_llm": result["constraints_llm"],
                    "type": result["type"],
                }
            )

        logging.info("Finish!!!")


if __name__ == "__main__":
    main()
