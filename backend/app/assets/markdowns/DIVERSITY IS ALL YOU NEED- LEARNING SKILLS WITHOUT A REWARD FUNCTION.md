## Diversity is All You Need: Learning Skills Without a Reward Function

**Diversity is All You Need (DIAYN)** is a reinforcement learning (RL) method for **unsupervised skill discovery**, enabling agents to autonomously learn diverse, reusable behaviors without external rewards. The approach leverages **mutual information maximization** and **maximum entropy policies** to encourage exploration and diversity, producing skills that can later be adapted for hierarchical RL, imitation learning, or fine-tuning on downstream tasks.

---

## Abstract

DIAYN introduces a framework for learning **diverse, task-agnostic skills** in RL agents without relying on predefined reward functions. The method maximizes an **information-theoretic objective** that encourages:
1. **Discriminability**: Skills should be distinguishable based on the states they visit.
2. **Diversity**: Skills should explore distinct regions of the state space.
3. **Exploration**: Policies should remain stochastic to avoid premature convergence.

Experiments on simulated robotic tasks (e.g., locomotion, navigation) demonstrate that DIAYN discovers interpretable skills (e.g., walking, jumping, flipping) **without any task-specific rewards**. These skills can then be:
- **Fine-tuned** to solve benchmark tasks faster than training from scratch.
- **Composed hierarchically** to tackle complex, sparse-reward problems.
- **Used for imitation learning** to replicate expert behaviors.

DIAYN addresses key challenges in RL, including **exploration in sparse-reward environments**, **sample efficiency**, and **hierarchical control**, by replacing hand-designed rewards with intrinsic diversity objectives.

---

## Introduction

### Motivation
Traditional RL requires **carefully designed reward functions** to elicit desired behaviors, which is often impractical for complex, real-world tasks. Intelligent agents (e.g., animals, humans) can explore and acquire skills **without explicit supervision**, later repurposing them for specific goals. DIAYN formalizes this idea by learning a **set of latent-conditioned policies (skills)** that maximize coverage of the state space while remaining distinguishable.

### Key Challenges
1. **Unsupervised Skill Learning**: How to define a useful objective when no reward function is provided?
2. **Diversity vs. Discriminability**: Skills must be both **distinct** (to cover the state space) and **robust** (to avoid collapsing into trivial behaviors).
3. **Scalability**: The method must work in high-dimensional, continuous control tasks (e.g., robotics).

### Solution Overview
DIAYN frames skill learning as maximizing the **mutual information** between skills (_Z_) and visited states (_S_), while regularizing with **entropy** to ensure exploration. The core objective is:
\[
F(\theta) = I(S; Z) + H[A|S] - I(A; Z|S)
\]
- **\(I(S; Z)\)**: Skills should predictably influence the states visited.
- **\(H[A|S]\)**: The mixture of all skills should act randomly (exploration).
- **\(-I(A; Z|S)\)**: Skills should not be distinguishable by actions alone (focus on states).

This objective is optimized using a **cooperative game** between:
- A **policy** \(\pi_\theta(a|s, z)\) conditioned on a latent skill \(z\).
- A **discriminator** \(q_\phi(z|s)\) that infers the skill from states.

---
## Related Work

### Hierarchical RL
Prior work on hierarchical RL (e.g., [Bacon et al., 2017](#bacon2017), [Florensa et al., 2017](#florensa2017)) learns skills to maximize a **known reward function**, often suffering from:
- **Meta-policy collapse**: The high-level controller ignores "bad" skills, starving them of gradients.
- **Task specificity**: Skills are optimized for a single reward, limiting reuse.

DIAYN avoids these issues by:
- Using a **random meta-policy** during unsupervised learning (all skills receive equal training).
- Learning **task-agnostic skills** that generalize across tasks.

### Intrinsic Motivation
Methods like **empowerment** ([Mohamed & Rezende, 2015](#mohamed2015)), **curiosity-driven exploration** ([Pathak et al., 2017](#pathak2017)), and **information gain** ([Houthooft et al., 2016](#houthooft2016)) use intrinsic rewards to explore. However, these typically learn **a single policy**, whereas DIAYN learns **many diverse policies**.

### Information Theory in RL
DIAYN builds on **maximum entropy RL** ([Haarnoja et al., 2018](#haarnoja2018)) and **variational intrinsic control (VIC)** ([Gregor et al., 2016](#gregor2016)), but improves scalability by:
1. **Fixing the skill prior** \(p(z)\) (uniform) to avoid the "Matthew Effect" (where diverse skills dominate training).
2. **Conditioning the discriminator on all states** (not just final states) for richer signals.
3. **Using off-policy RL** (Soft Actor-Critic) for stable training in high-dimensional spaces.

### Diversity Optimization
Neuroevolution methods (e.g., [Lehman & Stanley, 2011](#lehman2011)) maximize behavioral diversity but require **population-based search**, which is sample-inefficient. DIAYN achieves diversity with **gradient-based optimization** in a single agent.

---
## Method

### Core Objective
DIAYN maximizes:
\[
F(\theta) = \underbrace{I(S; Z)}_{\text{skills predict states}} + \underbrace{H[A|S]}_{\text{exploration}} - \underbrace{I(A; Z|S)}_{\text{skills distinguishable by states, not actions}}
\]
This is reparameterized as:
\[
F(\theta) = H[Z] - H[Z|S] + H[A|S, Z]
\]
- **\(H[Z]\)**: Maximized by using a **uniform prior** \(p(z)\).
- **\(-H[Z|S]\)**: Minimized by making skills **easily inferable** from states (via a discriminator \(q_\phi(z|s)\)).
- **\(H[A|S, Z]\)**: Maximized by using a **maximum entropy policy** (e.g., Soft Actor-Critic).

### Practical Implementation
1. **Skill Sampling**: At the start of each episode, sample a skill \(z \sim p(z)\) (uniform categorical).
2. **Policy Execution**: Act according to \(\pi_\theta(a|s, z)\) for the entire episode.
3. **Pseudo-Reward**: The reward for skill \(z\) at state \(s\) is:
   \[
   r_z(s) = \log q_\phi(z|s) - \log p(z)
   \]
   - This rewards states where the discriminator confidently predicts \(z\).
4. **Updates**:
   - **Policy**: Maximize \(r_z(s)\) + entropy regularization (via SAC).
   - **Discriminator**: Minimize cross-entropy to better predict \(z\) from \(s\).

### Algorithm
![Figure 1: DIAYN Algorithm](/app/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/tmp642rmt27.pdf-4-0.png)
*DIAYN alternates between updating the policy to visit discriminable states and updating the discriminator to infer skills from states.*

### Key Design Choices
1. **Fixed Prior \(p(z)\)**: Prevents collapse to a few skills (unlike VIC).
2. **State-Based Discrimination**: Avoids rewarding actions that don’t affect the environment (e.g., a robot gripping air).
3. **Entropy Regularization**: Ensures skills remain stochastic and explore.

---
## Experiments & Results

### Learned Skills
DIAYN discovers interpretable, diverse skills across tasks:

#### 1. Simple Navigation
![Figure 2a: 2D Navigation Skills](/app/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/tmp642rmt27.pdf-4-1.png)
*Skills in a 2D box partition the space into distinct regions.*

#### 2. Classic Control
- **Inverted Pendulum**: Learns to balance at different angles and oscillate with varying frequencies.
- **Mountain Car**: Discovers multiple strategies to climb the hill (e.g., different initial backups).

![Figure 18: Classic Control Skills](/app/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/tmp642rmt27.pdf-7-7.png)
*Skills for inverted pendulum (top) and mountain car (bottom) show diverse solutions.*

#### 3. Robotic Locomotion
![Figure 3: Locomotion Skills](/app/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/tmp642rmt27.pdf-4-2.png)
*Half-cheetah, hopper, and ant learn skills like running, jumping, flipping, and spinning without rewards.*

- **Half-Cheetah**: Runs forward/backward, flips, and falls.
- **Hopper**: Hops forward/backward, balances, or dives.
- **Ant**: Moves in arcs, spins, or flips.

### Training Dynamics
- Skills become **increasingly diverse** over time (Figure 2, right).
- The discriminator’s confidence (\(q_\phi(z|s)\)) grows, while entropy regularization prevents deterministic collapse (Figure 12).

![Figure 12: Training Objectives](/app/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/tmp642rmt27.pdf-7-1.png)
*Discriminability (orange) increases throughout training, while entropy (blue) plateaus.*

### Downstream Applications

#### 1. Policy Initialization
Pre-trained DIAYN skills **accelerate fine-tuning** on benchmark tasks compared to random initialization.

![Figure 5: Policy Initialization](/app/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/tmp642rmt27.pdf-5-0.png)
*Fine-tuning a DIAYN skill (orange) learns faster than training from scratch (blue).*

#### 2. Hierarchical RL
DIAYN skills serve as **primitives for hierarchical policies**:
- **2D Navigation**: A meta-controller selects skills to reach goals (Figure 6).
- **Cheetah Hurdle**: Composes skills to jump over obstacles (Figure 7, left).
- **Ant Navigation**: Solves sparse-reward waypoint tasks (Figure 7, right).

![Figure 7: Hierarchical RL](/app/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/tmp642rmt27.pdf-6-0.png)
*DIAYN + hierarchy outperforms baselines (TRPO, SAC, VIME) on sparse-reward tasks.*

#### 3. Imitation Learning
Given an expert trajectory, DIAYN retrieves the closest skill via:
\[
\hat{z} = \arg\max_z \prod_{s_t \in \tau^*} q_\phi(z|s_t)
\]
- Achieves **lower trajectory error** than baselines (Figure 22).
- The discriminator’s score \(q_\phi(\hat{z}|\tau^*)\) predicts imitation accuracy.

![Figure 22: Imitation Learning](/app/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/tmp642rmt27.pdf-12-1.png)
*DIAYN (red) matches expert trajectories more closely than baselines.*

### Comparisons to Baselines
| Method               | Skills Learned | Task Performance | Key Limitation                     |
|----------------------|----------------|------------------|------------------------------------|
| **DIAYN**            | Diverse, reusable | High             | None (fixed prior, max entropy)    |
| VIC ([Gregor et al., 2016](#gregor2016)) | Few skills dominate | Low              | Collapses to few skills            |
| VIME ([Houthooft et al., 2016](#houthooft2016)) | Single policy | Medium           | No hierarchical composition       |
| Random Initialization | None            | Low              | No pretraining benefit            |

---
## Conclusion

### Summary of Contributions
1. **Unsupervised Skill Learning**: DIAYN learns diverse, task-agnostic skills **without rewards** by maximizing mutual information and entropy.
2. **Empirical Validation**: Skills solve benchmark tasks (e.g., locomotion) despite never seeing task rewards.
3. **Downstream Utility**: Skills improve:
   - **Sample efficiency** via policy initialization.
   - **Exploration** in sparse-reward tasks via hierarchy.
   - **Imitation learning** by matching expert trajectories.
4. **Scalability**: Works in high-dimensional robotic tasks (e.g., 111-DoF ant).

### Broader Impact
- **Exploration**: Reduces reliance on handcrafted rewards.
- **Hierarchical RL**: Provides reusable primitives for complex tasks.
- **Real-World Applications**: Potential for robotics, animation, and interactive AI (e.g., game NPCs).

### Future Directions
- **Combining with Reward Augmentation**: Jointly optimize intrinsic (diversity) and extrinsic (task) rewards.
- **Human-in-the-Loop**: Use human feedback to select useful skills.
- **Multi-Agent Skills**: Extend to collaborative or competitive settings.

---
## References

- <a name="achiam2017"></a>Achiam, J., Edwards, H., Amodei, D., & Abbeel, P. (2017). *Variational autoencoding learning of options by reinforcement*. NIPS Deep RL Symposium.
- <a name="agakov2004"></a>Agakov, F. (2004). *The IM algorithm: A variational approach to information maximization*. NeurIPS.
- <a name="bacon2017"></a>Bacon, P. L., Harb, J., & Precup, D. (2017). *The option-critic architecture*. AAAI.
- <a name="baranes2013"></a>Baranes, A., & Oudeyer, P. Y. (2013). *Active learning of inverse models with intrinsically motivated goal exploration in robots*. Robotics and Autonomous Systems.
- <a name="bellemare2016"></a>Bellemare, M. G., et al. (2016). *Unifying count-based exploration and intrinsic motivation*. NeurIPS.
- <a name="bishop2016"></a>Bishop, C. M. (2016). *Pattern Recognition and Machine Learning*. Springer.
- <a name="brockman2016"></a>Brockman, G., et al. (2016). *OpenAI Gym*. arXiv:1606.01540.
- <a name="christiano2017"></a>Christiano, P. F., et al. (2017). *Deep reinforcement learning from human preferences*. NeurIPS.
- <a name="dayan1993"></a>Dayan, P., & Hinton, G. E. (1993). *Feudal reinforcement learning*. NeurIPS.
- <a name="duan2016"></a>Duan, Y., et al. (2016). *Benchmarking deep reinforcement learning for continuous control*. ICML.
- <a name="florensa2017"></a>Florensa, C., Duan, Y., & Abbeel, P. (2017). *Stochastic neural networks for hierarchical reinforcement learning*. arXiv:1704.03012.
- <a name="frans2017"></a>Frans, K., et al. (2017). *Meta learning shared hierarchies*. arXiv:1710.09767.
- <a name="fu2017"></a>Fu, J., Co-Reyes, J., & Levine, S. (2017). *EX2: Exploration with exemplar models for deep reinforcement learning*. NeurIPS.
- <a name="gregor2016"></a>Gregor, K., Rezende, D. J., & Wierstra, D. (2016). *Variational intrinsic control*. arXiv:1611.07507.
- <a name="gu2017"></a>Gu, S., et al. (2017). *Deep reinforcement learning for robotic manipulation*. ICRA.
- <a name="haarnoja2018"></a>Haarnoja, T., et al. (2018). *Soft actor-critic: Off-policy maximum entropy deep reinforcement learning*. arXiv:1801.01290.
- <a name="hadfield2017"></a>Hadfield-Menell, D., et al. (2017). *Inverse reward design*. NeurIPS.
- <a name="hausman2018"></a>Hausman, K., et al. (2018). *Learning an embedding space for transferable robot skills*. ICLR.
- <a name="heess2016"></a>Heess, N., et al. (2016). *Learning and transfer of modulated locomotor controllers*. arXiv:1610.05182.
- <a name="henderson2017"></a>Henderson, P., et al. (2017). *Deep reinforcement learning that matters*. arXiv:1709.06560.
- <a name="houthooft2016"></a>Houthooft, R., et al. (2016). *VIME: Variational information maximizing exploration*. NeurIPS.
- <a name="jung2011"></a>Jung, T., Polani, D., & Stone, P. (2011). *Empowerment for continuous agent-environment systems*. Adaptive Behavior.
- <a name="krishnan2017"></a>Krishnan, S., et al. (2017). *DDCO: Discovery of deep continuous options for robot learning from demonstrations*. CoRL.
- <a name="lehman2011a"></a>Lehman, J., & Stanley, K. O. (2011a). *Abandoning objectives: Evolution through the search for novelty alone*. Evolutionary Computation.
- <a name="merton1968"></a>Merton, R. K. (1968). *The Matthew effect in science*. Science.
- <a name="mirowski2016"></a>Mirowski, P., et al. (2016). *Learning to navigate in complex environments*. arXiv:1611.03673.
- <a name="mnih2013"></a>Mnih, V., et al. (2013). *Playing Atari with deep reinforcement learning*. arXiv:1312.5602.
- <a name="mohamed2015"></a>Mohamed, S., & Rezende, D. J. (2015). *Variational information maximisation for intrinsically motivated reinforcement learning*. NeurIPS.
- <a name="mouret2009"></a>Mouret, J. B., & Doncieux, S. (2009). *Overcoming the bootstrap problem in evolutionary robotics*. CEC.
- <a name="nachum2017"></a>Nachum, O., et al. (2017). *Bridging the gap between value and policy based reinforcement learning*. NeurIPS.
- <a name="oudeyer2007"></a>Oudeyer, P. Y., Kaplan, F., & Hafner, V. V. (2007). *Intrinsic motivation systems for autonomous mental development*. IEEE TEVC.
- <a name="pathak2017"></a>Pathak, D., et al. (2017). *Curiosity-driven exploration by self-supervised prediction*. arXiv:1705.05363.
- <a name="pong2018"></a>Pong, V., et al. (2018). *Temporal difference models: Model-free deep RL for model-based control*. arXiv:1802.09081.
- <a name="ryan2000"></a>Ryan, R. M., & Deci, E. L. (2000). *Intrinsic and extrinsic motivations*. Contemporary Educational Psychology.
- <a name="schmidhuber2010"></a>Schmidhuber, J. (2010). *Formal theory of creativity, fun, and intrinsic motivation*. IEEE TAMD.
- <a name="schulman2015a"></a>Schulman, J., et al. (2015a). *Trust region policy optimization*. ICML.
- <a name="schulman2017"></a>Schulman, J., et al. (2017). *Equivalence between policy gradients and soft Q-learning*. arXiv:1704.06440.
- <a name="shazeer2017"></a>Shazeer, N., et al. (2017). *Outrageously large neural networks*. arXiv:1701.06538.
- <a name="silver2016"></a>Silver, D., et al. (2016). *Mastering the game of Go with deep neural networks*. Nature.
- <a name="such2017"></a>Such, F. P., et al. (2017). *Deep neuroevolution*. arXiv:1712.06567.
- <a name="sukhbaatar2017"></a>Sukhbaatar, S., et al. (2017). *Intrinsic motivation and automatic curricula via asymmetric self-play*. arXiv:1703.05407.
- <a name="woolley2011"></a>Woolley, B. G., & Stanley, K. O. (2011). *On the deleterious effects of a priori objectives on evolution*. GECCO.
- <a name="zhu2017"></a>Zhu, Y., et al. (2017). *Target-driven visual navigation in indoor scenes*. ICRA.
- <a name="ziebart2008"></a>Ziebart, B. D., et al. (2008). *Maximum entropy inverse reinforcement learning*. AAAI.