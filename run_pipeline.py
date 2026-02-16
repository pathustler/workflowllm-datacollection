from generate.generate_workflows import generate_workflows
from filter.validate_workflow import validate
from expand.expand_queries import expand_queries
from enrich.generate_comments import generate_comments
from enrich.generate_plan import generate_plan
from enrich.generate_query import generate_query
from dataset.build_dataset import build_dataset


def main():
    print("▶️ Generating synthetic workflows...")
    generate_workflows(
        input_path="shortcuts_enriched.json",
        output_path="data/workflows_raw.json"
    )

    print("▶️ Validating workflows...")
    validate(
        input_path="data/workflows_raw.json",
        output_path="data/workflows_valid.json"
    )

    print("▶️ Expanding queries...")
    expand_queries(
        input_path="data/workflows_valid.json",
        output_path="data/workflows_expanded.json"
    )

    print("▶️ Generating comments...")
    generate_comments(
        input_path="data/workflows_expanded.json",
        output_path="data/workflows_commented.json"
    )

    print("▶️ Generating plans...")
    generate_plan(
        input_path="data/workflows_commented.json",
        output_path="data/workflows_planned.json"
    )

    print("▶️ Generating queries...")
    generate_query(
        input_path="data/workflows_planned.json",
        output_path="data/workflows_queried.json"
    )

    print("▶️ Building final dataset...")
    build_dataset(
        input_path="data/workflows_queried.json",
        output_path="data/workflowbench.json"
    )

    print("✅ Pipeline complete!")


if __name__ == "__main__":
    main()
