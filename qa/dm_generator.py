import json
import time
from typing import Dict, List

import requests

BASE_URL = "https://api.ai71.ai/v1/"
API_KEY = "ai71-api-b89a083e-a1f7-4539-b18e-25f1b4d1bbd5"


class DMGenerator:

    @staticmethod
    def check_budget():
        resp = requests.get(
            f"{BASE_URL}check_budget",
            headers={"Authorization": f"Bearer {API_KEY}"},
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def bulk_generate(n_questions: int, question_categorizations: List[Dict], user_categorizations: List[Dict]):
        resp = requests.post(
            f"{BASE_URL}bulk_generation",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "n_questions": n_questions,
                "question_categorizations": question_categorizations,
                "user_categorizations": user_categorizations
            }
        )
        resp.raise_for_status()
        request_id = resp.json()["request_id"]
        print(json.dumps(resp.json(), indent=4))

        results = DMGenerator._wait_for_generation_to_finish(request_id)

        return results

    @staticmethod
    def _wait_for_generation_to_finish(request_id: str):
        while True:
            resp = requests.get(
                f"{BASE_URL}fetch_generation_results",
                headers={"Authorization": f"Bearer {API_KEY}"},
                params={"request_id": request_id},
            )
            resp.raise_for_status()
            if resp.json()["status"] == "completed":
                print(json.dumps(resp.json(), indent=4))
                return resp.json()
            else:
                print("Waiting for generation to finish...")
                time.sleep(5)
    @staticmethod
    def extract_generation_results(results):
        """take a request results and output Q&A pairs as a list"""
        response = requests.get(results["file"])
        qas = [json.loads(line) for line in response.text.splitlines()]
        return qas

    @staticmethod
    def get_all_requests():
        resp = requests.get(
            f"{BASE_URL}get_all_requests",
            headers={"Authorization": f"Bearer {API_KEY}"},
        )
        resp.raise_for_status()
        print(json.dumps(resp.json(), indent=4))