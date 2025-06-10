import json
import requests
from tqdm import tqdm
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from multiprocessing import Process, Queue
import numpy as np


def process_worker(task_queue, done_queue, worker_func, proc_id, **kwargs):
    for line in iter(task_queue.get, "STOP"):
        result = worker_func(line, proc_id, **kwargs)
        done_queue.put(result)
    done_queue.put("COMPLETE")

def process_and_save_results(results, save_path):
    if (len(results)) % 100 == 0:
        with open(save_path, mode='a', encoding='utf-8', errors='ignore') as writer:
            for result in results:
                writer.write(json.dumps(result, ensure_ascii=False) + '\n')
        results = []
    return results

def process_and_save_results(results, save_path):
    if (len(results)) % 100 == 0:
        with open(save_path, mode='a', encoding='utf-8', errors='ignore') as writer:
            for result in results:
                writer.write(json.dumps(result, ensure_ascii=False) + '\n')
        results = []
    return results

def map_with_save_and_progress(f: callable, xs: list[Any], num_threads: int = 100, save_path='save_data', condition=None, **kwargs):
    num_processes = num_threads
    QUEUE_SIZE = 3000
    task_queue, done_queue = Queue(maxsize=QUEUE_SIZE), Queue(maxsize=QUEUE_SIZE)

    def read_data_into_queue():
        for line in xs:
            task_queue.put(line)
        for _ in range(num_processes):
            task_queue.put('STOP')

    processes = []
    for p_id in range(num_processes):
        process = Process(target=process_worker, args=(task_queue, done_queue, f, p_id), kwargs=kwargs)
        process.start()
        processes.append(process)

    process = Process(target=read_data_into_queue)
    process.start()

    progress_bar = tqdm(total=len(xs))
    num_finished = 0
    d_len = 0
    results = []
    while num_finished < num_processes:
        item = done_queue.get()
        if item == 'COMPLETE':
            num_finished += 1
            
        else:
            if (condition is not None and condition(item)) or condition is None:
                d_len += 1
                results.append(item)
        
            results = process_and_save_results(results, save_path)
            progress_bar.set_description(f'Num of Valid: {d_len})')
            progress_bar.update(1)

    with open(save_path, mode='a', encoding='utf-8', errors='ignore') as writer:
        for result in results:
            writer.write(json.dumps(result, ensure_ascii=False) + '\n')
    progress_bar.close()
    return results, d_len


def write_jsonl_file(data, file_path):
    with open(file_path, 'w', encoding= 'utf-8') as f:
        for line in data:
            f.write(json.dumps(line) + '\n')


def read_jsonl_file(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                json_data = json.loads(line)
                data.append(json_data)
            except json.JSONDecodeError as e:
                print(f"Skipping line due to decoding error: {e}")
                continue
    return data


def read_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")
        return None
    return data

def get_response(url, headers, payload, timeout = 300):
    max_retries = 20
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json().get('choices', [{}])[0].get('message', {}).get('content', "")
        except Exception as e:
            if attempt == max_retries - 1:  
                print(f"All {max_retries} attempts failed. Last error: {e}")
        time.sleep(1)
    return None