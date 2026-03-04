"""
Seed technical questions for Data Science & AI interviews.

Usage:
    /Users/mohdsaif/Desktop/interview_automation/.venv/bin/python seed_technical_questions.py
"""

import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

from app.core.config import settings


QUESTIONS = [
    {
        "title": "Bias-Variance Tradeoff",
        "description": """## Bias-Variance Tradeoff

Explain the bias-variance tradeoff in machine learning.

- What is bias? What is variance?
- How do they affect model performance?
- Give an example of a high-bias model and a high-variance model.
- How would you balance the two when building a predictive model?

**Provide a detailed, well-structured answer.**""",
        "category": "AI_ML",
        "difficulty": "medium",
        "time_limit_sec": 600,
    },
    {
        "title": "Overfitting and Regularization",
        "description": """## Overfitting and Regularization

What is overfitting in machine learning? How can you detect and prevent it?

Please cover:
- Definition of overfitting with an example
- Techniques to prevent overfitting (e.g., regularization, dropout, cross-validation)
- The difference between L1 (Lasso) and L2 (Ridge) regularization
- When would you choose one over the other?

**Provide a detailed, well-structured answer.**""",
        "category": "AI_ML",
        "difficulty": "medium",
        "time_limit_sec": 600,
    },
    {
        "title": "Gradient Descent Variants",
        "description": """## Gradient Descent Variants

Explain the different variants of gradient descent used in training neural networks.

Cover the following:
- Batch Gradient Descent
- Stochastic Gradient Descent (SGD)
- Mini-batch Gradient Descent
- What are the advantages and disadvantages of each?
- Briefly explain adaptive optimizers like Adam and RMSProp.

**Provide a detailed, well-structured answer.**""",
        "category": "DEEP_LEARNING",
        "difficulty": "medium",
        "time_limit_sec": 600,
    },
    {
        "title": "Precision, Recall, and F1 Score",
        "description": """## Precision, Recall, and F1 Score

Explain precision, recall, and F1 score in the context of classification problems.

- Define each metric with formulas.
- When would you prioritize precision over recall, and vice versa? Give real-world examples.
- What is the F1 score and when is it useful?
- How does the ROC-AUC curve differ from precision-recall curves?

**Provide a detailed, well-structured answer.**""",
        "category": "DATA_SCIENCE",
        "difficulty": "easy",
        "time_limit_sec": 600,
    },
    {
        "title": "Transformers and Attention Mechanism",
        "description": """## Transformers and Attention Mechanism

Explain the Transformer architecture and the self-attention mechanism.

Cover the following:
- What problem do Transformers solve that RNNs and LSTMs struggle with?
- Explain the self-attention mechanism (Query, Key, Value).
- What is multi-head attention and why is it useful?
- Briefly describe how models like BERT and GPT use the Transformer architecture differently.

**Provide a detailed, well-structured answer.**""",
        "category": "NLP",
        "difficulty": "hard",
        "time_limit_sec": 600,
    },
    {
        "title": "Feature Engineering for Tabular Data",
        "description": """## Feature Engineering for Tabular Data

Describe common feature engineering techniques for tabular/structured data.

Cover the following:
- Handling missing values (imputation strategies)
- Encoding categorical variables (one-hot, label encoding, target encoding)
- Feature scaling and normalization
- Feature selection methods (filter, wrapper, embedded)
- Creating interaction features

**Provide a detailed, well-structured answer with examples.**""",
        "category": "DATA_SCIENCE",
        "difficulty": "medium",
        "time_limit_sec": 600,
    },
    {
        "title": "CNNs for Image Classification",
        "description": """## CNNs for Image Classification

Explain how Convolutional Neural Networks (CNNs) work for image classification.

Cover the following:
- What is a convolution operation and what does it capture?
- Explain pooling layers and their purpose.
- What is the role of fully connected layers at the end?
- Describe common CNN architectures (LeNet, AlexNet, VGG, ResNet) and their key innovations.
- What is transfer learning and how is it applied with CNNs?

**Provide a detailed, well-structured answer.**""",
        "category": "DEEP_LEARNING",
        "difficulty": "medium",
        "time_limit_sec": 600,
    },
    {
        "title": "Hypothesis Testing",
        "description": """## Hypothesis Testing

Explain the concept of hypothesis testing in statistics.

Cover the following:
- Null hypothesis vs alternative hypothesis
- Type I and Type II errors
- p-value and significance level (alpha)
- Steps to perform a hypothesis test
- Give an example of a real-world scenario where you would use hypothesis testing.

**Provide a detailed, well-structured answer.**""",
        "category": "STATISTICS",
        "difficulty": "medium",
        "time_limit_sec": 600,
    },
    {
        "title": "Random Forests vs Gradient Boosting",
        "description": """## Random Forests vs Gradient Boosting

Compare and contrast Random Forest and Gradient Boosting algorithms.

Cover the following:
- How does each algorithm build its ensemble of trees?
- Key differences in training (bagging vs boosting)
- Strengths and weaknesses of each
- When would you choose one over the other?
- Mention popular implementations (XGBoost, LightGBM, CatBoost).

**Provide a detailed, well-structured answer.**""",
        "category": "AI_ML",
        "difficulty": "medium",
        "time_limit_sec": 600,
    },
    {
        "title": "Cross-Validation Strategies",
        "description": """## Cross-Validation Strategies

Explain different cross-validation strategies and when to use each.

Cover the following:
- K-Fold Cross-Validation
- Stratified K-Fold
- Leave-One-Out Cross-Validation (LOOCV)
- Time-Series Split
- Why is cross-validation important, and what problems does it solve?
- When might standard K-Fold be inappropriate?

**Provide a detailed, well-structured answer.**""",
        "category": "DATA_SCIENCE",
        "difficulty": "easy",
        "time_limit_sec": 600,
    },
]


async def seed_questions():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM technical_questions"))
        count = result.scalar()
        if count > 0:
            print(f"[SKIP] {count} technical questions already exist.")
            await engine.dispose()
            return

        for q in QUESTIONS:
            await conn.execute(
                text("""
                    INSERT INTO technical_questions (id, title, description, category, difficulty, time_limit_sec, created_at)
                    VALUES (:id, :title, :description, :category, :difficulty, :time_limit_sec, NOW())
                """),
                {
                    "id": uuid.uuid4(),
                    "title": q["title"],
                    "description": q["description"],
                    "category": q["category"],
                    "difficulty": q["difficulty"],
                    "time_limit_sec": q["time_limit_sec"],
                },
            )
            print(f"  [OK] Seeded: {q['title']}")

    print(f"\n[OK] Successfully seeded {len(QUESTIONS)} technical questions.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_questions())
