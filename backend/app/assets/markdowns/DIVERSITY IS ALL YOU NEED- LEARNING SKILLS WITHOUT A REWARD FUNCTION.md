# Diversity Is All You Need: Learning Skills Without a Reward Function

## 1) Lead
"Diversity Is All You Need" (DIAYN) is a method for learning useful skills without a reward function. This approach allows intelligent agents to explore their environments and learn a variety of behaviors, which can be useful for future tasks. The method has been shown to work effectively in several simulated robotic tasks, where it learns diverse skills such as walking and jumping. These skills can be used as a pretraining step for more complex tasks, helping to overcome challenges in exploration and data efficiency in reinforcement learning.

## 2) What problem it solves
Learning skills without a reward function is important for several reasons. In environments with sparse rewards, learning useful skills can help the agent reach goal states more efficiently. Skills learned without supervision can also serve as primitives for hierarchical reinforcement learning, shortening the episode length for complex tasks. Additionally, unsupervised learning of skills can reduce the need for human feedback in environments where evaluating the reward is costly. Finally, when given an unfamiliar environment, unsupervised skill discovery can help determine what tasks the agent should be able to learn.

## 3) The core idea (plain-language intuition)
The core idea behind DIAYN is to maximize the diversity of skills that an agent can learn. The method encourages the agent to explore different states in the environment and learn skills that are distinguishable from each other. By doing so, the agent can cover a wide range of possible behaviors, which can be useful for future tasks. The method uses a discriminator to ensure that each skill is distinct and a maximum entropy policy to encourage exploration.

## 4) How it works (step-by-step, conceptual)
1. **Initialization**: The agent starts with a set of skills, each represented by a latent variable.
2. **Exploration**: The agent explores the environment using these skills, visiting different states.
3. **Discrimination**: A discriminator is used to distinguish between the different skills based on the states visited.
4. **Reward Calculation**: The agent receives a pseudo-reward based on how well the discriminator can distinguish between the skills.
5. **Policy Update**: The agent updates its policy to maximize the pseudo-reward, encouraging it to explore more diverse states.
6. **Discriminator Update**: The discriminator is updated to better distinguish between the skills.
7. **Repeat**: Steps 2-6 are repeated until the agent has learned a diverse set of skills.

## 5) What you get out of it (what skills look like)
The skills learned by DIAYN are diverse and distinct. For example, in a simulated robot environment, the agent might learn skills such as walking, running, jumping, and flipping. These skills are not learned with the intention of solving a specific task but rather to explore the environment in different ways. The skills can be used as a pretraining step for more complex tasks, providing a good parameter initialization for downstream tasks.

## 6) Limitations and common misunderstandings
- **Limitation**: The method may not scale well to very high-dimensional environments or tasks with a large number of possible skills.
- **Common Misunderstanding**: It is important to note that the skills learned by DIAYN are not intended to solve specific tasks. Instead, they are learned to explore the environment in different ways. The skills may incidentally solve tasks, but this is not the primary goal of the method.

## 7) Related ideas (brief, non-technical)
- **Hierarchical Reinforcement Learning**: DIAYN can be used to learn skills that serve as primitives for hierarchical reinforcement learning, where a meta-controller selects which skill to execute.
- **Imitation Learning**: The skills learned by DIAYN can be used to imitate expert demonstrations, allowing the agent to follow the expert's behavior in the environment.
- **Exploration Bonuses**: DIAYN can be compared to methods that use exploration bonuses to encourage the agent to visit new states, although DIAYN focuses on learning diverse skills rather than maximizing a single exploration objective.

## 8) References
- Eysenbach, B., Gupta, A., Ibarz, J., Levine, S. (2018). Diversity Is All You Need: Learning Skills Without a Reward Function. arXiv preprint arXiv:1802.06072.