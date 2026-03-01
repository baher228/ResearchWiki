# Diversity Is All You Need (DIAYN)

## 1) Lead
"Diversity Is All You Need (DIAYN)" is a research paper that introduces a novel approach to unsupervised skill discovery in reinforcement learning (RL). The paper proposes a method for learning diverse and predictable skills without any extrinsic reward. This approach combines model-based and model-free learning to discover skills that are easy to predict, making them suitable for planning and composition in downstream tasks.

## 2) What problem it solves
Traditional model-based reinforcement learning (MBRL) aims to learn a global model of the environment's dynamics. However, learning an accurate model for complex systems is challenging and may not generalize well outside the training distribution. DIAYN addresses this by discovering predictable skills that can be used for planning, even without an accurate global model. This approach allows for more flexible and effective planning in complex environments.

## 3) The core idea (plain-language intuition)
The core idea of DIAYN is to learn skills that are both diverse and predictable. The method encourages the discovery of skills that produce distinct and predictable transitions in the environment. By focusing on predictability, the learned skills can be easily composed for planning purposes. This is achieved by maximizing the mutual information between the next state and the current skill, conditioned on the current state.

## 4) How it works (step-by-step, conceptual)
1. **Initialization**: Initialize the policy and the skill-dynamics model.
2. **Skill Sampling**: Sample a skill from a prior distribution at the beginning of each episode.
3. **Data Collection**: Collect new data by interacting with the environment using the current policy.
4. **Model Update**: Update the skill-dynamics model using the collected data to better predict the next state given the current state and skill.
5. **Reward Computation**: Compute the intrinsic reward for each transition, which encourages predictability and diversity.
6. **Policy Update**: Update the policy using any RL algorithm to maximize the intrinsic reward.
7. **Repeat**: Repeat the process until convergence.

## 5) What you get out of it (what skills look like)
The skills learned by DIAYN are diverse and predictable behaviors. For example, in a robotics environment, the skills might include different gaits for walking, running, or navigating. These skills are learned without any extrinsic reward, purely through exploration and the maximization of predictability and diversity.

## 6) Limitations and common misunderstandings
- **Limitation**: The method relies on the assumption that the environment's dynamics can be reasonably approximated by the skill-dynamics model. If the environment is too complex or stochastic, the learned skills may not be as predictable.
- **Common Misunderstanding**: It is important to note that the skills learned by DIAYN are not explicitly designed to be useful for any specific task. They are learned purely for their predictability and diversity, and their usefulness for downstream tasks is a secondary benefit.

## 7) Related ideas (brief, non-technical)
- **Intrinsic Motivation**: DIAYN is related to methods that use intrinsic motivation to drive exploration in RL. These methods encourage the agent to explore the environment by maximizing some form of intrinsic reward, such as curiosity or novelty.
- **Hierarchical Reinforcement Learning (HRL)**: The skills learned by DIAYN can be seen as a form of temporal abstraction, similar to options in HRL. These skills can be composed to solve more complex tasks.
- **Model-Based RL**: DIAYN builds on model-based RL by learning a model of the environment's dynamics, but it focuses on learning predictable skills rather than a global model.

## 8) References
- **DIAYN Paper**: Sharma, A., Gu, S., Levine, S., Kumar, V., & Hausman, K. (2020). Dynamics-Aware Unsupervised Discovery of Skills. In ICLR 2020.