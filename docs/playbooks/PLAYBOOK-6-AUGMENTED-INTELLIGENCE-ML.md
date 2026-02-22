# Playbook 6: Augmented Intelligence for Machine Learning
## NLKE v3.0 - Rapid ML Development with Self-Referential AI Systems

**Version:** 1.0
**Last Updated:** November 8, 2025
**Audience:** ML Engineers, Data Scientists, AI Researchers
**Prerequisites:** ML fundamentals, Python programming, basic Claude API knowledge
**Related Playbooks:** [PB 1](PLAYBOOK-1-COST-OPTIMIZATION.md) (costs), [PB 4](PLAYBOOK-4-KNOWLEDGE-ENGINEERING.md) (KG), [PB 8](PLAYBOOK-8-CONTINUOUS-LEARNING-LOOP.md) (persistence), [PB 9](PLAYBOOK-9-METACOGNITION-WORKFLOWS.md) (metacognition)

---

## Table of Contents

1. [Overview](#overview)
2. [NLKE v3.0 Philosophy](#nlke-v30-philosophy)
3. [Pattern Library](#pattern-library)
4. [Rapid ML Prototyping](#rapid-ml-prototyping)
5. [Data Preparation & Labeling](#data-preparation--labeling)
6. [Feature Engineering](#feature-engineering)
7. [Model Evaluation & Testing](#model-evaluation--testing)
8. [ML Pipeline Development](#ml-pipeline-development)
9. [Hyperparameter Optimization](#hyperparameter-optimization)
10. [ML Debugging & Optimization](#ml-debugging--optimization)
11. [Self-Referential Systems](#self-referential-systems)
12. [Production Patterns](#production-patterns)
13. [Cost Optimization](#cost-optimization)
14. [Troubleshooting](#troubleshooting)
15. [Real-World Use Cases](#real-world-use-cases)

---

## Overview

### What is Augmented Intelligence for ML?

**Augmented Intelligence** is the NLKE methodology for using AI (Claude) to accelerate machine learning development. Unlike traditional "AI for ML" approaches, NLKE emphasizes **Self-Referential Augmented Intelligence Systems (SRAIS)** - systems that can represent and reason about their own operation, enabling AI to understand and collaborate with the system.

**Core Principle:** Build WITH AI, Document AS you build.

### Key Capabilities

Claude excels at ML tasks requiring:
- **Rapid Prototyping**: From idea to working prototype in hours, not days
- **Data Understanding**: Analyzing datasets, identifying patterns, suggesting features
- **Code Generation**: ML pipelines, training scripts, evaluation frameworks
- **Debugging**: Identifying model issues, data leakage, training problems
- **Optimization**: Hyperparameter tuning, architecture search, performance improvements
- **Documentation**: Living documentation that stays synchronized with experiments

### Why Claude for ML Development?

1. **Context Understanding**: 200K tokens = entire datasets, experiments, codebases
2. **Extended Thinking**: Deep reasoning for complex ML decisions
3. **Multi-Modal**: Analyze data visualizations, model architectures, training curves
4. **Tool Use**: Direct integration with ML frameworks (PyTorch, TensorFlow, sklearn)
5. **Self-Referential**: Can understand and reason about your ML system's architecture

### Playbook Goals

By the end of this playbook, you will:

- Prototype ML solutions 10x faster using augmented intelligence
- Build self-referential ML systems that AI can understand and collaborate with
- Automate data preparation, labeling, and feature engineering
- Generate comprehensive evaluation frameworks automatically
- Debug and optimize models efficiently
- Create living ML documentation
- Integrate Claude into your ML workflow seamlessly

---

## NLKE v3.0 Philosophy

### Self-Referential Augmented Intelligence Systems (SRAIS)

**Definition**: Systems that can represent and reason about their own operation, enabling AI to understand and use the system collaboratively.

**Traditional Approach:**
```
Human writes ML code → Human debugs → Human optimizes → Human documents
```

**SRAIS Approach:**
```
Human + Claude design system → Claude generates code → Claude + Human debug →
Claude optimizes → Claude documents → System is self-documenting and AI-navigable
```

### Key Principles

**1. Representational Transparency**
- ML pipelines documented as knowledge graphs
- Experiments tracked in AI-readable format
- System architecture explainable to Claude

**2. Collaborative Development**
- Claude as active collaborator, not just code generator
- Continuous feedback loop between human intuition and AI reasoning
- Extended thinking for complex ML decisions

**3. Living Documentation**
- Documentation generated during development
- Experiments auto-documented with rationale
- Knowledge base grows with every iteration

**4. Cost-Optimized Iteration**
- Prompt caching for dataset schemas, model architectures
- Batch processing for evaluation runs
- 90-95% cost savings on repetitive ML tasks

---

## Pattern Library

### Official Examples Used in This Playbook

| Example | Category | Purpose | Location |
|---------|----------|---------|----------|
| Extended Thinking - Basic | Extended Thinking | ML architecture decisions | Week 1-2 Examples |
| Streaming Extended Thinking | Extended Thinking | Real-time experiment analysis | Week 1-2 Examples |
| Tool Use with Extended Thinking | Extended Thinking | ML framework integration | Week 1-2 Examples |
| Prompt Caching - Large Context | Prompt Caching | Cache datasets/experiments | Week 1-2 Examples |
| Batch API - Multiple Evaluations | Batch Processing | Parallel model evaluation | Week 1-2 Examples |

### Pattern Combinations for ML Development

```
Pattern: Dataset Analysis → Feature Engineering
- Prompt Caching for dataset schema
- Extended Thinking for feature selection
- Tool Use for feature computation

Pattern: Model Training → Evaluation
- Prompt Caching for model architecture
- Batch Processing for hyperparameter search
- Extended Thinking for result interpretation

Pattern: Experiment Tracking → Optimization
- Self-referential experiment logs
- Claude reads past experiments
- Suggests next experiments based on history
```

---

## Rapid ML Prototyping

### From Idea to Prototype in Hours

**Goal**: Build complete ML solution from problem description

```python
import anthropic
import os

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def design_ml_solution(
    problem_description: str,
    dataset_sample: str,
    constraints: dict = None
):
    """
    Design complete ML solution using extended thinking.

    Args:
        problem_description: Business problem to solve
        dataset_sample: Sample of available data (first N rows)
        constraints: Optional constraints (latency, accuracy, cost)

    Returns:
        Complete ML solution design with architecture, code, evaluation plan
    """
    if constraints is None:
        constraints = {
            "max_latency_ms": 100,
            "min_accuracy": 0.90,
            "deployment": "cloud"
        }

    constraints_text = "\n".join([f"- {k}: {v}" for k, v in constraints.items()])

    prompt = f"""Design a complete machine learning solution for this problem.

Problem:
{problem_description}

Data Sample (first rows):
```
{dataset_sample}
```

Constraints:
{constraints_text}

Using extended thinking, analyze:
1. **Problem Type**: Classification, regression, clustering, etc.
2. **Data Quality**: Missing values, imbalance, outliers
3. **Feature Engineering**: What features to create
4. **Model Selection**: Which algorithms to try and why
5. **Evaluation Strategy**: Metrics, validation approach
6. **Production Considerations**: Scalability, latency, maintenance

Provide:
1. **Architecture Design**: Complete ML system architecture
2. **Data Pipeline**: Data loading, cleaning, feature engineering code
3. **Model Code**: Training and inference code (scikit-learn/PyTorch)
4. **Evaluation Framework**: Comprehensive evaluation code
5. **Experiment Plan**: Which experiments to run and in what order
6. **Documentation**: README explaining the solution

Return as structured JSON with code blocks.
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=16000,
        thinking={
            "type": "enabled",
            "budget_tokens": 8000
        },
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract thinking and solution
    thinking_content = ""
    solution_content = ""

    for block in response.content:
        if block.type == "thinking":
            thinking_content = block.thinking
        elif block.type == "text":
            solution_content = block.text

    import json
    if "```json" in solution_content:
        solution_content = solution_content.split("```json")[1].split("```")[0]

    solution = json.loads(solution_content.strip())
    solution["reasoning"] = thinking_content

    return solution


# Example Usage
problem = """
We need to predict customer churn for a subscription service.
Customers can cancel anytime. We want to identify high-risk customers
before they churn so we can intervene with retention offers.
"""

dataset_sample = """
customer_id,tenure_months,monthly_spend,support_tickets,last_login_days,churned
C001,12,49.99,2,3,0
C002,3,29.99,5,45,1
C003,24,79.99,1,1,0
C004,6,49.99,8,30,1
C005,18,99.99,0,2,0
"""

solution = design_ml_solution(problem, dataset_sample)

print("Architecture:", solution["architecture_design"])
print("\nData Pipeline:")
print(solution["data_pipeline_code"])
print("\nModel Code:")
print(solution["model_code"])
```

**Expected Output**:
- Complete data preprocessing pipeline
- Feature engineering code (recency, frequency, monetary)
- Model training code (LogisticRegression + RandomForest + XGBoost comparison)
- Evaluation framework (precision/recall/F1, ROC curves)
- Experiment plan (baseline → feature engineering → model selection → hyperparameter tuning)

---

## Data Preparation & Labeling

### Intelligent Data Cleaning

**Goal**: Clean and validate datasets automatically

```python
def analyze_and_clean_data(
    dataframe_info: str,
    sample_rows: str,
    cleaning_strategy: str = "conservative"
):
    """
    Analyze data quality and generate cleaning code.

    Args:
        dataframe_info: df.info() output
        sample_rows: df.head(10).to_string()
        cleaning_strategy: 'conservative' or 'aggressive'

    Returns:
        Pandas code to clean the dataset
    """
    prompt = f"""Analyze this dataset and generate cleaning code.

DataFrame Info:
{dataframe_info}

Sample Rows:
{sample_rows}

Cleaning Strategy: {cleaning_strategy}
- conservative: Only fix obvious errors, keep most data
- aggressive: Remove ambiguous data, prioritize quality

Identify and fix:
1. **Missing Values**: Strategy for each column (drop, impute, flag)
2. **Data Types**: Incorrect types (strings that should be dates, etc.)
3. **Outliers**: Statistical outliers that should be removed/capped
4. **Duplicates**: Exact duplicates or near-duplicates
5. **Invalid Values**: Out-of-range values, impossible combinations
6. **Encoding Issues**: Text encoding problems

Generate Python pandas code that:
- Explains each cleaning step in comments
- Logs number of rows affected
- Creates validation reports
- Is reversible (saves original data)

Return complete cleaning pipeline as Python function.
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8192,
        thinking={
            "type": "enabled",
            "budget_tokens": 3000
        },
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract code
    answer = ""
    for block in response.content:
        if block.type == "text":
            answer = block.text

    return answer
```

### Automated Data Labeling

**Goal**: Generate labels for unlabeled data using Claude

```python
def generate_labels_batch(
    unlabeled_samples: List[str],
    labeling_guidelines: str,
    label_schema: Dict
):
    """
    Generate labels for unlabeled data in batch.

    Args:
        unlabeled_samples: List of text samples to label
        labeling_guidelines: Instructions for labeling
        label_schema: Label definitions and examples

    Returns:
        Labeled data with confidence scores
    """
    schema_text = json.dumps(label_schema, indent=2)

    # Create batch requests
    batch_requests = []

    for i, sample in enumerate(unlabeled_samples):
        batch_requests.append({
            "custom_id": f"label-{i}",
            "params": {
                "model": "claude-sonnet-4-5-20250929",
                "max_tokens": 1024,
                "system": [{
                    "type": "text",
                    "text": f"Labeling Guidelines:\n{labeling_guidelines}\n\nLabel Schema:\n{schema_text}",
                    "cache_control": {"type": "ephemeral"}
                }],
                "messages": [{
                    "role": "user",
                    "content": f"""Label this sample according to the guidelines.

Sample:
{sample}

Return JSON:
{{
  "label": "label_value",
  "confidence": 0.95,
  "reasoning": "why this label was chosen"
}}
"""
                }]
            }
        })

    # Submit batch (50% cost savings)
    message_batch = client.messages.batches.create(requests=batch_requests)

    # Poll for completion
    import time
    while True:
        batch_status = client.messages.batches.retrieve(message_batch.id)
        if batch_status.processing_status == "ended":
            break
        time.sleep(10)

    # Collect labeled results
    labeled_data = []
    for result in client.messages.batches.results(message_batch.id):
        if result.result.type == "succeeded":
            content = result.result.message.content[0].text

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]

            label_result = json.loads(content.strip())
            labeled_data.append(label_result)

    return labeled_data


# Example: Sentiment labeling
samples = [
    "This product is amazing! Best purchase ever.",
    "Terrible quality. Broke after 2 days.",
    "It's okay, nothing special."
]

guidelines = "Classify sentiment as positive, negative, or neutral based on overall tone."

schema = {
    "positive": {"description": "Clearly positive sentiment", "examples": ["great", "love it"]},
    "negative": {"description": "Clearly negative sentiment", "examples": ["terrible", "worst"]},
    "neutral": {"description": "Mixed or neutral sentiment", "examples": ["okay", "average"]}
}

labels = generate_labels_batch(samples, guidelines, schema)

# Result: Labels for all samples with confidence scores
# Cost: 50% off (batch) + 90% off (cached guidelines) = 95% savings!
```

---

## Feature Engineering

### Intelligent Feature Discovery

**Goal**: Discover relevant features from raw data

```python
def discover_features(
    dataset_description: str,
    target_variable: str,
    sample_data: str,
    domain_knowledge: str = ""
):
    """
    Discover and generate feature engineering code.

    Args:
        dataset_description: Description of available data
        target_variable: What we're trying to predict
        sample_data: Sample rows from dataset
        domain_knowledge: Optional domain-specific insights

    Returns:
        Feature engineering code + rationale
    """
    domain_context = f"\n\nDomain Knowledge:\n{domain_knowledge}" if domain_knowledge else ""

    prompt = f"""Design feature engineering strategy for this ML problem.

Dataset:
{dataset_description}

Sample Data:
{sample_data}

Target Variable: {target_variable}
{domain_context}

Using extended thinking, identify:
1. **Derived Features**: Features to compute from existing columns
2. **Interaction Features**: Combinations that might be predictive
3. **Temporal Features**: If timestamps available (day of week, seasonality)
4. **Aggregation Features**: Group-by aggregations if entity-level data
5. **Encoding Strategies**: How to handle categorical variables
6. **Scaling/Normalization**: Which features need normalization

Generate Python code that:
- Creates all suggested features
- Explains WHY each feature might be useful
- Handles missing values in feature computation
- Validates feature distributions
- Returns feature importance analysis code

Include both the feature engineering code AND the reasoning.
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8192,
        thinking={
            "type": "enabled",
            "budget_tokens": 5000
        },
        messages=[{"role": "user", "content": prompt}]
    )

    thinking = ""
    code = ""

    for block in response.content:
        if block.type == "thinking":
            thinking = block.thinking
        elif block.type == "text":
            code = block.text

    return {
        "feature_code": code,
        "reasoning": thinking
    }
```

---

## Model Evaluation & Testing

### Comprehensive Evaluation Framework

**Goal**: Generate complete model evaluation code

```python
def generate_evaluation_framework(
    problem_type: str,  # 'classification', 'regression', 'ranking'
    model_info: str,
    dataset_characteristics: str
):
    """
    Generate comprehensive model evaluation code.

    Args:
        problem_type: Type of ML problem
        model_info: Model architecture/type
        dataset_characteristics: Class imbalance, size, etc.

    Returns:
        Complete evaluation code with metrics, visualizations, reports
    """
    prompt = f"""Generate comprehensive evaluation framework for this {problem_type} problem.

Model:
{model_info}

Dataset Characteristics:
{dataset_characteristics}

Create Python code that evaluates the model using:

1. **Metrics**:
   - Primary metrics (accuracy, F1, RMSE, etc. based on problem type)
   - Secondary metrics for comprehensive view
   - Business metrics if applicable

2. **Visualizations**:
   - Confusion matrix (classification)
   - ROC/PR curves (binary classification)
   - Prediction vs actual (regression)
   - Residual plots (regression)
   - Feature importance
   - Learning curves

3. **Statistical Tests**:
   - Cross-validation with confidence intervals
   - Bootstrap confidence intervals
   - Statistical significance tests

4. **Error Analysis**:
   - Error distribution analysis
   - Identify systematic errors
   - Per-class/segment performance

5. **Model Comparison**:
   - Compare multiple models
   - Generate comparison tables
   - Statistical comparison tests

6. **Report Generation**:
   - Markdown evaluation report
   - Summary statistics
   - Recommendations for improvement

Return complete Python code using scikit-learn, matplotlib, seaborn.
Include docstrings and inline comments.
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=12000,
        thinking={
            "type": "enabled",
            "budget_tokens": 4000
        },
        messages=[{"role": "user", "content": prompt}]
    )

    answer = ""
    for block in response.content:
        if block.type == "text":
            answer = block.text

    return answer
```

---

## ML Pipeline Development

### End-to-End Pipeline Generation

**Goal**: Generate production-ready ML pipeline

```python
def generate_ml_pipeline(
    pipeline_spec: dict,
    ml_framework: str = "sklearn"
):
    """
    Generate complete ML pipeline from specification.

    Args:
        pipeline_spec: Pipeline configuration
        ml_framework: 'sklearn', 'pytorch', 'tensorflow'

    Returns:
        Complete pipeline code with training, inference, monitoring
    """
    spec_text = json.dumps(pipeline_spec, indent=2)

    prompt = f"""Generate production-ready ML pipeline for {ml_framework}.

Pipeline Specification:
{spec_text}

Create complete pipeline with:

1. **Data Pipeline**:
   - Data loading from various sources
   - Validation checks
   - Preprocessing transformations
   - Feature engineering
   - Train/val/test splitting

2. **Training Pipeline**:
   - Model initialization
   - Training loop with checkpointing
   - Validation during training
   - Early stopping
   - Model saving

3. **Inference Pipeline**:
   - Model loading
   - Batch and streaming inference
   - Output post-processing
   - Confidence scoring

4. **Monitoring**:
   - Data drift detection
   - Performance monitoring
   - Resource usage tracking
   - Alerting logic

5. **Configuration Management**:
   - Config files for all parameters
   - Environment-based configs (dev/staging/prod)
   - Version tracking

6. **Testing**:
   - Unit tests for each component
   - Integration tests
   - Performance tests

7. **Documentation**:
   - Usage examples
   - API documentation
   - Deployment guide

Generate modular, maintainable code following ML engineering best practices.
Include error handling, logging, and type hints.
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=16000,
        thinking={
            "type": "enabled",
            "budget_tokens": 6000
        },
        messages=[{"role": "user", "content": prompt}]
    )

    pipeline_code = ""
    for block in response.content:
        if block.type == "text":
            pipeline_code = block.text

    return pipeline_code


# Example Usage
spec = {
    "problem": "customer_churn_prediction",
    "data_source": "postgresql",
    "features": ["tenure", "usage_metrics", "support_interactions"],
    "model_type": "gradient_boosting",
    "serving": "rest_api",
    "monitoring": ["data_drift", "performance_degradation"]
}

pipeline = generate_ml_pipeline(spec, ml_framework="sklearn")
```

---

## Hyperparameter Optimization

### Intelligent Hyperparameter Search

**Goal**: Design hyperparameter search strategy

```python
def design_hyperparameter_search(
    model_type: str,
    dataset_size: int,
    training_time_budget: str,
    past_experiments: List[Dict] = None
):
    """
    Design hyperparameter search strategy based on constraints.

    Args:
        model_type: Model algorithm
        dataset_size: Number of training samples
        training_time_budget: Time available (e.g., "2 hours", "1 day")
        past_experiments: Optional previous experiment results

    Returns:
        Search strategy + code to execute it
    """
    experiments_context = ""
    if past_experiments:
        experiments_context = "\n\nPast Experiments:\n" + json.dumps(past_experiments, indent=2)

    prompt = f"""Design hyperparameter optimization strategy.

Model: {model_type}
Dataset Size: {dataset_size:,} samples
Time Budget: {training_time_budget}
{experiments_context}

Using extended thinking, determine:
1. **Search Strategy**: Grid search, random search, Bayesian optimization, or Hyperband
2. **Parameter Priorities**: Which hyperparameters matter most
3. **Search Space**: Ranges for each hyperparameter
4. **Evaluation Strategy**: Cross-validation folds, metric to optimize
5. **Resource Allocation**: How many trials within time budget
6. **Early Stopping**: Criteria to abandon poor configurations

Generate Python code using optuna/scikit-learn that:
- Implements the recommended search strategy
- Logs all trials with parameters and results
- Tracks best configuration
- Generates visualization of search progress
- Saves results for future reference

If past experiments provided, use them to narrow search space.
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8192,
        thinking={
            "type": "enabled",
            "budget_tokens": 4000
        },
        messages=[{"role": "user", "content": prompt}]
    )

    thinking = ""
    code = ""

    for block in response.content:
        if block.type == "thinking":
            thinking = block.thinking
        elif block.type == "text":
            code = block.text

    return {
        "search_strategy_reasoning": thinking,
        "search_code": code
    }
```

---

## ML Debugging & Optimization

### Systematic Debugging

**Goal**: Debug ML model issues systematically

```python
def debug_ml_model(
    model_description: str,
    training_code: str,
    symptoms: str,
    training_curves: str = ""
):
    """
    Debug ML model issues using extended thinking.

    Args:
        model_description: Model architecture/type
        training_code: Code used for training
        symptoms: Observed problems (overfitting, poor performance, etc.)
        training_curves: Optional training/validation loss curves

    Returns:
        Diagnosis + fixes
    """
    curves_context = f"\n\nTraining Curves:\n{training_curves}" if training_curves else ""

    prompt = f"""Debug this machine learning model issue.

Model:
{model_description}

Training Code:
```python
{training_code}
```

Symptoms:
{symptoms}
{curves_context}

Using extended thinking, systematically diagnose:

1. **Data Issues**:
   - Data leakage (using future information)
   - Train/test distribution mismatch
   - Class imbalance
   - Insufficient data
   - Noisy labels

2. **Model Issues**:
   - Underfitting (model too simple)
   - Overfitting (model too complex)
   - Poor architecture choice
   - Initialization problems
   - Gradient issues (vanishing/exploding)

3. **Training Issues**:
   - Learning rate problems
   - Optimization algorithm issues
   - Batch size effects
   - Regularization too weak/strong

4. **Feature Engineering Issues**:
   - Missing important features
   - Feature scaling problems
   - Feature leakage

For each potential issue:
- Explain why it might be the cause
- Provide diagnostic code to verify
- Suggest specific fixes

Rank issues by likelihood and provide step-by-step debugging plan.
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=12000,
        thinking={
            "type": "enabled",
            "budget_tokens": 6000
        },
        messages=[{"role": "user", "content": prompt}]
    )

    thinking = ""
    diagnosis = ""

    for block in response.content:
        if block.type == "thinking":
            thinking = block.thinking
        elif block.type == "text":
            diagnosis = block.text

    return {
        "reasoning_process": thinking,
        "diagnosis_and_fixes": diagnosis
    }
```

---

## Self-Referential Systems

### Building AI-Readable ML Experiments

**Goal**: Create experiment logs that Claude can read and reason about

```python
class SelfReferentialMLExperiment:
    """
    ML experiment that documents itself for future AI collaboration.
    Follows NLKE v3.0 SRAIS principles.
    """

    def __init__(self, experiment_name: str, anthropic_api_key: str):
        self.experiment_name = experiment_name
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.experiment_log = {
            "experiment_name": experiment_name,
            "created_at": datetime.now().isoformat(),
            "dataset": {},
            "preprocessing": [],
            "features": [],
            "models": [],
            "results": [],
            "insights": []
        }

    def log_dataset(self, dataset_info: Dict):
        """Log dataset with AI-readable description."""
        self.experiment_log["dataset"] = {
            **dataset_info,
            "description": self._generate_description(
                f"Dataset with {dataset_info.get('n_samples')} samples, "
                f"{dataset_info.get('n_features')} features"
            )
        }

    def log_preprocessing_step(self, step_name: str, step_code: str, rationale: str):
        """Log preprocessing with rationale."""
        self.experiment_log["preprocessing"].append({
            "step": step_name,
            "code": step_code,
            "rationale": rationale,
            "timestamp": datetime.now().isoformat()
        })

    def log_feature(self, feature_name: str, formula: str, rationale: str):
        """Log feature with creation rationale."""
        self.experiment_log["features"].append({
            "name": feature_name,
            "formula": formula,
            "rationale": rationale
        })

    def log_model_result(self, model_name: str, hyperparameters: Dict,
                         metrics: Dict, training_notes: str):
        """Log model with complete context."""
        self.experiment_log["models"].append({
            "name": model_name,
            "hyperparameters": hyperparameters,
            "metrics": metrics,
            "training_notes": training_notes,
            "timestamp": datetime.now().isoformat()
        })

    def ask_claude_for_next_experiment(self):
        """
        Ask Claude to suggest next experiment based on current results.
        This is SRAIS in action: Claude reads experiment log and suggests next steps.
        """
        # Create cached experiment context
        experiment_context = json.dumps(self.experiment_log, indent=2)

        prompt = """Based on these experiment results, suggest the next experiment to run.

Analyze:
1. Current best model and its limitations
2. Patterns in what worked vs what didn't
3. Unexplored hypotheses
4. Potential improvements

Suggest:
- Next experiment to try
- Expected improvement
- Specific hyperparameters/features to test
- Rationale for this choice

Return structured JSON with experiment suggestion.
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            system=[{
                "type": "text",
                "text": f"Experiment Log:\n{experiment_context}",
                "cache_control": {"type": "ephemeral"}
            }],
            thinking={
                "type": "enabled",
                "budget_tokens": 3000
            },
            messages=[{"role": "user", "content": prompt}]
        )

        suggestion = ""
        for block in response.content:
            if block.type == "text":
                suggestion = block.text

        return suggestion

    def _generate_description(self, content: str) -> str:
        """Generate AI-readable description."""
        return f"[AUTO-GENERATED] {content}"

    def save_experiment(self, filepath: str):
        """Save experiment log as JSON."""
        with open(filepath, 'w') as f:
            json.dump(self.experiment_log, f, indent=2)


# Usage Example
exp = SelfReferentialMLExperiment(
    "churn_prediction_v1",
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
)

# Log experiment steps
exp.log_dataset({"n_samples": 10000, "n_features": 15, "target": "churned"})
exp.log_preprocessing_step(
    "impute_missing",
    "df.fillna(df.median())",
    "Median imputation chosen over mean due to outliers in usage_minutes"
)
exp.log_feature(
    "recency_score",
    "days_since_last_login / tenure_days",
    "Recency relative to tenure captures engagement decline"
)
exp.log_model_result(
    "RandomForest",
    {"n_estimators": 100, "max_depth": 10},
    {"f1": 0.76, "precision": 0.82, "recall": 0.71},
    "Good precision but missing 29% of churners"
)

# Ask Claude for next experiment
next_exp = exp.ask_claude_for_next_experiment()
print("Claude suggests:")
print(next_exp)

# Save for future reference
exp.save_experiment("experiments/churn_v1.json")
```

---

## Production Patterns

### Complete Augmented ML Workflow

```python
class AugmentedMLWorkflow:
    """
    Complete ML workflow with Claude augmentation at every stage.
    Demonstrates NLKE v3.0 principles in production.
    """

    def __init__(self, project_name: str, anthropic_api_key: str):
        self.project_name = project_name
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.experiments = []

    def stage_1_data_exploration(self, dataset_path: str):
        """Stage 1: Explore dataset with Claude assistance."""
        import pandas as pd

        df = pd.read_csv(dataset_path)

        # Get basic info
        info_str = df.info(buf=None)
        sample_str = df.head(20).to_string()
        desc_str = df.describe().to_string()

        # Ask Claude for insights
        prompt = f"""Analyze this dataset and suggest ML approach.

Dataset Info:
{info_str}

Sample Rows:
{sample_str}

Statistical Summary:
{desc_str}

Provide:
1. Data quality assessment
2. Suggested preprocessing steps
3. Feature engineering ideas
4. Model recommendations
5. Potential challenges
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=8192,
            thinking={
                "type": "enabled",
                "budget_tokens": 4000
            },
            messages=[{"role": "user", "content": prompt}]
        )

        insights = ""
        for block in response.content:
            if block.type == "text":
                insights = block.text

        return insights

    def stage_2_feature_engineering(self, dataset, claude_suggestions: str):
        """Stage 2: Generate features based on Claude's suggestions."""
        # Parse Claude's suggestions and generate feature code
        prompt = f"""Based on these suggestions, generate Python code for feature engineering.

Suggestions:
{claude_suggestions}

Generate complete pandas code that creates all suggested features.
Include error handling and validation.
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        feature_code = ""
        for block in response.content:
            if block.type == "text":
                feature_code = block.text

        # Execute feature engineering code
        # In production, use safe exec or generate to file and review
        return feature_code

    def stage_3_model_training(self, X_train, y_train):
        """Stage 3: Train models with hyperparameter optimization."""
        # Use Claude to design search strategy
        search_strategy = self._get_search_strategy(X_train.shape, y_train.value_counts().to_dict())

        # Execute search (implementation from hyperparameter optimization section)
        # ...

        return search_results

    def stage_4_evaluation(self, model, X_test, y_test):
        """Stage 4: Comprehensive evaluation with Claude's analysis."""
        # Generate evaluation code (from evaluation section)
        eval_code = generate_evaluation_framework("classification", str(type(model)), "balanced")

        # Execute evaluation
        # ...

        # Ask Claude to interpret results
        interpretation = self._interpret_results(evaluation_results)

        return interpretation

    def stage_5_production_prep(self, model, evaluation_report: str):
        """Stage 5: Prepare for production deployment."""
        prompt = f"""Based on this evaluation, prepare production deployment checklist.

Evaluation Report:
{evaluation_report}

Create checklist for:
1. Model serialization and versioning
2. API endpoint design
3. Input validation
4. Monitoring and alerting
5. Rollback strategy
6. Documentation

Return structured JSON checklist.
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            thinking={
                "type": "enabled",
                "budget_tokens": 2000
            },
            messages=[{"role": "user", "content": prompt}]
        )

        checklist = ""
        for block in response.content:
            if block.type == "text":
                checklist = block.text

        return checklist
```

---

## Cost Optimization

### Cost Breakdown for ML Development

**Typical Costs** (Claude Sonnet 4.5):

| Task | Input Tokens | Output Tokens | Cost | Frequency |
|------|--------------|---------------|------|-----------|
| Dataset Analysis | 3,000 | 2,000 | $0.039 | Once per dataset |
| Feature Engineering | 2,000 | 3,000 | $0.051 | Per iteration |
| Model Evaluation | 1,500 | 4,000 | $0.065 | Per model |
| Hyperparameter Search | 1,000 | 2,000 | $0.033 | Per experiment |
| Debugging Session | 2,500 | 3,000 | $0.053 | As needed |

### Optimization Strategies

**1. Cache Dataset/Experiment Context (90% savings)**
```python
# Cache dataset schema and experiment log
system=[{
    "type": "text",
    "text": experiment_context,  # Reused across all queries
    "cache_control": {"type": "ephemeral"}
}]

# First query: ~$0.05
# Next 10 queries: ~$0.005 each (90% savings)
```

**2. Batch Evaluation Runs (50% savings)**
```python
# Evaluate multiple models in batch
batch_requests = [create_eval_request(model) for model in models]
batch = client.messages.batches.create(requests=batch_requests)

# Standard: $0.65 for 10 models
# Batch: $0.33 for 10 models (50% savings)
```

**3. Combined: Caching + Batch (95% savings)**
```python
# Batch with cached experiment context
# Standard: $0.65 for 10 models
# Optimized: ~$0.03 for 10 models (95% savings!)
```

### Real-World Cost Example

**Scenario**: ML project with 50 experiments over 2 weeks

| Strategy | Cost | Notes |
|----------|------|-------|
| No optimization | $100+ | Individual API calls |
| With caching | $10-15 | Cache experiment context |
| With batch | $50-60 | Batch evaluations |
| **Caching + Batch** | **$5-8** | **95% savings** |

---

## Troubleshooting

### Common ML Issues

**Issue: Claude suggests impractical features**
- **Solution**: Provide computational constraints in prompt
- **Example**: "Features must compute in < 100ms per sample"

**Issue: Generated code has bugs**
- **Solution**: Ask Claude to add unit tests + validation
- **Pattern**: "Generate code WITH comprehensive tests"

**Issue: Model evaluation incomplete**
- **Solution**: Specify business metrics explicitly
- **Context**: "Optimize for precision at 90% recall (cost of false negatives is high)"

**Issue: Hyperparameter search inefficient**
- **Solution**: Provide past experiment results to narrow search
- **SRAIS**: Feed experiment log back to Claude

---

## Real-World Use Cases

### Use Case 1: Customer Churn Prediction (Day 1 to Production)

**Timeline**: 8 hours (vs 2-3 weeks traditional)

```python
# Hour 1-2: Data exploration + feature engineering
insights = design_ml_solution(problem, dataset_sample)

# Hour 3-4: Model training + evaluation
eval_framework = generate_evaluation_framework(...)

# Hour 5-6: Hyperparameter optimization
search_strategy = design_hyperparameter_search(...)

# Hour 7-8: Production preparation
deployment_checklist = stage_5_production_prep(...)

# Result: Production-ready model in 1 day
```

**Cost**: ~$2-3 with caching + batch (vs $50+ without optimization)

### Use Case 2: Automated Data Labeling (10K samples)

```python
# Traditional: 40 hours of human labeling
# Augmented: 2 hours with Claude batch labeling

labels = generate_labels_batch(samples_10k, guidelines, schema)

# Cost: ~$15 (batch + caching = 95% off)
# Time saved: 38 hours
# ROI: $15 for 38 hours of work = incredible value
```

### Use Case 3: ML Pipeline Modernization

```python
# Migrate legacy sklearn pipeline to modern PyTorch
legacy_code = open("old_pipeline.py").read()

modern_pipeline = generate_ml_pipeline(
    extract_pipeline_spec(legacy_code),
    ml_framework="pytorch"
)

# Result: Modern pipeline with monitoring, testing, documentation
# Time: 4 hours (vs 2-3 weeks rewriting from scratch)
```

---

## Summary

### Key Takeaways

1. **SRAIS Principle**: Build systems Claude can understand and collaborate with
2. **10x Faster**: Prototype to production in days, not weeks
3. **95% Cost Savings**: Caching + batch for ML workflows
4. **Living Documentation**: Experiments document themselves
5. **Continuous Collaboration**: Claude suggests next experiments based on results

### Augmented Intelligence Workflow

```
Human defines problem →
Claude designs solution →
Human validates approach →
Claude generates code →
System documents itself →
Claude analyzes results →
Claude suggests improvements →
Repeat until production-ready
```

### Cost-Optimized ML Development

**Expected Costs** (complete ML project):
- Without optimization: $100-200
- With optimization: $5-10 (95% savings)
- Time savings: 10x faster development

### Next Steps

1. Set up self-referential experiment logging
2. Use Claude for dataset analysis and feature discovery
3. Generate evaluation frameworks automatically
4. Build experiment history that Claude can read
5. Let Claude suggest next experiments based on results
6. Deploy with confidence using generated deployment checklists

---

## Additional Resources

**See Also (Playbooks)**:
- **[Playbook 1: Cost Optimization](PLAYBOOK-1-COST-OPTIMIZATION.md)** - Caching + batch patterns
- **[Playbook 4: Knowledge Engineering](PLAYBOOK-4-KNOWLEDGE-ENGINEERING.md)** - Experiment tracking as KG
- **[Playbook 8: Continuous Learning Loop](PLAYBOOK-8-CONTINUOUS-LEARNING-LOOP.md)** - Persistent model insights
- **[Playbook 9: Metacognition Workflows](PLAYBOOK-9-METACOGNITION-WORKFLOWS.md)** - Validated ML decisions

**ML Frameworks**:
- scikit-learn for classical ML
- PyTorch/TensorFlow for deep learning
- Optuna for hyperparameter optimization
- MLflow for experiment tracking

**NLKE v3.0**:
- MANIFEST.md for SRAIS documentation
- Self-referential system principles
- Build WITH AI, Document AS you build

---

**Playbook Version**: 1.0
**Last Updated**: November 8, 2025
**Methodology**: NLKE v3.0 - Self-Referential Augmented Intelligence Systems
**Maintained By**: NLKE Project
**Feedback**: Submit issues or suggestions to project repository

