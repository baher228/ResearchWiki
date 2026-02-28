## Dynamics-Aware Unsupervised Discovery of Skills (DADS)

**ICLR 2020 Paper** by Archit Sharma, Shixiang Gu, Sergey Levine, Vikash Kumar, and Karol Hausman (Google Brain).

**GitHub**: [https://github.com/google-research/dads](https://github.com/google-research/dads)

---

## Abstract

**Dynamics-Aware Discovery of Skills (DADS)** is an **unsupervised reinforcement learning (RL)** framework that discovers **predictable, diverse skills** while learning their **dynamics models**. Unlike traditional **model-based RL (MBRL)**, which struggles to learn a single global dynamics model for complex environments, DADS learns a **skill-conditioned policy** and a corresponding **skill-dynamics model**. This enables **zero-shot planning** in the learned skill space, outperforming both MBRL and **goal-conditioned RL** on sparse-reward tasks. DADS leverages **mutual information maximization** to ensure skills are **diverse** and **predictable**, making them composable for hierarchical control.

Key contributions:
- Unsupervised discovery of **infinitely many skills** in continuous spaces.
- **Zero-shot planning** in the skill space for downstream tasks.
- Outperforms MBRL and hierarchical RL baselines on complex locomotion tasks.

---

## Introduction

### Challenges in Model-Based RL
Traditional **model-based RL (MBRL)** learns a **global dynamics model** to predict state transitions for any action. However, this approach faces two key challenges:
1. **Complexity**: Learning an accurate model for high-dimensional, discontinuous dynamics (e.g., humanoid locomotion) is computationally intensive.
2. **Generalization**: Models often fail outside the training state distribution, limiting their utility for new tasks.

### Key Insight: Skill-Conditioned Dynamics
Instead of a single global model, DADS learns:
- A **skill-conditioned policy** \( \pi(a | s, z) \), where \( z \) is a latent skill variable.
- A **skill-dynamics model** \( q(s' | s, z) \), predicting transitions for a specific skill \( z \).

This decomposition simplifies modeling by focusing on **local, skill-specific dynamics** rather than global transitions.

### Unsupervised Skill Discovery
DADS discovers skills **without extrinsic rewards** by optimizing for:
1. **Diversity**: Skills should cover a wide range of behaviors (e.g., walking forward/backward, turning).
2. **Predictability**: Transitions under a skill \( z \) should be consistent and easy to model.

The learned skills and dynamics enable **zero-shot planning** for downstream tasks via **model-predictive control (MPC)** in the skill space.

---

## Related Work

### Skill Discovery via Mutual Information
Prior work uses **mutual information (MI)** to encourage diverse skill discovery:
- **DIAYN** (Eysenbach et al., 2018): Maximizes MI between skills and states to ensure discriminability.
- **VIC** (Gregor et al., 2016): Uses variational MI to learn controllable features.

DADS extends this by optimizing for **predictability** alongside diversity, making skills more useful for hierarchical composition.

### Intrinsic Motivation
Methods like **empowerment** (Klyubin et al., 2005) and **curiosity-driven exploration** (Pathak et al., 2017) encourage agents to explore novel states. DADS differs by focusing on **predictable transitions** rather than novelty alone.

### Hierarchical RL (HRL)
HRL methods (Sutton et al., 1999; Bacon et al., 2017) decompose tasks into **temporal abstractions** (options/skills). DADS provides a **two-phase approach**:
1. **Unsupervised pre-training**: Learn skills and their dynamics.
2. **Planning phase**: Compose skills for downstream tasks.

### Model-Based Planning
DADS builds on **MBRL** techniques (Deisenroth & Rasmussen, 2011; Chua et al., 2018) but simplifies dynamics modeling by conditioning on skills. It uses **Model Predictive Path Integral (MPPI)** (Williams et al., 2016) for planning.

---

## Method

### Overview
DADS jointly optimizes:
1. A **skill-conditioned policy** \( \pi(a | s, z) \).
2. A **skill-dynamics model** \( q_\phi(s' | s, z) \).

The objective maximizes the **conditional mutual information** \( I(s'; z | s) \), which decomposes into:
- **Diversity**: Maximize entropy \( H(s' | s) \) (exploration).
- **Predictability**: Minimize entropy \( H(s' | s, z) \) (consistent transitions for each skill).

### Optimization
The algorithm alternates between:
1. **Fitting the dynamics model** \( q_\phi \) to minimize \( D_{KL}(p(s' | s, z) || q_\phi(s' | s, z)) \).
2. **Updating the policy** \( \pi \) to maximize the variational lower bound of \( I(s'; z | s) \).

The **intrinsic reward** for the policy is:
\[
r_z(s, a, s') = \log q_\phi(s' | s, z) - \log \sum_{i=1}^L q_\phi(s' | s, z_i), \quad z_i \sim p(z)
\]
This encourages:
- **Predictability**: High \( q_\phi(s' | s, z) \) (transitions match the model).
- **Diversity**: Low \( \sum_i q_\phi(s' | s, z_i) \) (transitions differ from other skills).

### Skill Spaces
- **Discrete**: One-hot vectors for \( z \) (e.g., 20 skills for Ant).
- **Continuous**: \( z \sim \text{Uniform}(-1, 1)^D \) (e.g., \( D=2 \) for Ant, \( D=5 \) for Humanoid).

### Planning with Skill Dynamics
At test time, DADS uses **MPPI** to plan in the skill space:
1. Sample skill sequences \( \{z_1, \dots, z_{HP}\} \) from a Gaussian distribution.
2. Simulate trajectories using \( q_\phi(s' | s, z) \).
3. Select the sequence with the highest reward and execute \( z_1 \) for \( H_Z \) steps.
4. Repeat until the task is completed.

**Algorithm 2** (Latent Space Planner):
![Figure 3: Latent space planner overview](/app/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/tmpp0nv6uzq.pdf-5-0.png)
*Caption: The planner refines skill sequences via MPPI, simulating trajectories with \( q_\phi \) and updating the plan distribution based on rewards.*

---

## Experiments & Results

### Qualitative Analysis
DADS discovers diverse skills **without extrinsic rewards**:
- **Half-Cheetah**: Forward/backward running, turning.
- **Ant**: Omnidirectional walking, turning.
- **Humanoid**: Stable gaits, direction changes.

![Figure 4: Learned skills in MuJoCo environments](/app/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/tmpp0nv6uzq.pdf-5-1.png)
*Caption: Visualization of unsupervised skills for Half-Cheetah, Ant, and Humanoid.*

#### Continuous vs. Discrete Skills
Continuous skill spaces enable **smoother interpolation** between behaviors:
![Figure 5: Ant skill trajectories in continuous vs. discrete spaces](/app/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/tmpp0nv6uzq.pdf-5-2.png)
*Caption: (Left/Center) X-Y traces show greater diversity in continuous spaces. (Right) Heatmap of trajectory orientation vs. skill \( z \), demonstrating smooth interpolation.*

### Skill Variance Analysis
DADS skills exhibit **lower variance** than **DIAYN** (which optimizes only for diversity):
![Figure 6: Standard deviation of Ant's position](/app/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/tmpp0nv6uzq.pdf-7-2.png)
*Caption: DADS skills (with/without x-y prior) have lower variance than DIAYN, improving composability.*

### Model-Based RL Comparison
DADS outperforms **PETS** (Chua et al., 2018) in zero-shot planning for Ant navigation:
- **Random-MBRL**: Trained on random trajectories.
- **Weak-Oracle MBRL**: Trained on goal-directed trajectories.
- **Strong-Oracle MBRL**: Trained on a fixed goal.

![Figure 7: Zero-shot planning performance](/app/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/tmpp0nv6uzq.pdf-6-1.png)
*Caption: DADS (continuous/discrete) outperforms MBRL baselines, even when they are trained on the test task.*

### Hierarchical Control
DADS skills are **composable** for hierarchical RL:
- **Hierarchical DIAYN**: Fails to compose high-variance skills.
- **Hierarchical DADS**: Successfully navigates to goals.

![Figure 8: Hierarchical control performance](/app/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/tmpp0nv6uzq.pdf-8-1.png)
*Caption: (Left) Meta-controller fails with DIAYN skills but succeeds with DADS. (Right) DADS generalizes better than goal-conditioned RL (GCRL) on sparse/dense rewards.*

### Goal-Conditioned RL
DADS generalizes better than **goal-conditioned RL** (GCRL) on sparse-reward navigation:
- **Dense reward**: DADS degrades gracefully with goal distance; GCRL fails outside its training distribution.
- **Sparse reward**: GCRL fails entirely; DADS maintains performance.

---

## Conclusion

DADS introduces a **scalable, unsupervised method** for discovering **predictable, diverse skills** and their dynamics. Key takeaways:
1. **Unsupervised learning**: Skills are learned without extrinsic rewards.
2. **Zero-shot planning**: Composes skills for downstream tasks via MPC.
3. **Outperformance**: Surpasses MBRL and hierarchical RL baselines on complex locomotion tasks.
4. **Generalization**: Handles sparse rewards and long-horizon planning better than goal-conditioned RL.

Future work includes:
- Extending to **off-policy data** (e.g., via relabeling tricks).
- Applying to **manipulation tasks** and **vision-based control**.

---

## References

- Abadi, M., Agarwal, A., et al. (2015). TensorFlow: Large-scale machine learning on heterogeneous systems. [http://tensorflow.org/](http://tensorflow.org/)
- Achiam, J., Edwards, H., et al. (2018). Variational option discovery algorithms. *arXiv:1807.10299*.
- Bacon, P.-L., Harb, J., & Precup, D. (2017). The option-critic architecture. *AAAI*.
- Bellemare, M., et al. (2016). Unifying count-based exploration and intrinsic motivation. *NeurIPS*.
- Brockman, G., et al. (2016). OpenAI Gym. *arXiv:1606.01540*.
- Chua, K., et al. (2018). Deep reinforcement learning in a handful of trials using probabilistic dynamics models. *NeurIPS*.
- Deisenroth, M. P., & Rasmussen, C. E. (2011). PILCO: A model-based and data-efficient approach to policy search. *ICML*.
- Eysenbach, B., et al. (2018). Diversity is all you need: Learning skills without a reward function. *arXiv:1802.06070*.
- Florensa, C., Duan, Y., & Abbeel, P. (2017). Stochastic neural networks for hierarchical reinforcement learning. *arXiv:1704.03012*.
- Gregor, K., Rezende, D. J., & Wierstra, D. (2016). Variational intrinsic control. *arXiv:1611.07507*.
- Gu, S., et al. (2017). Deep reinforcement learning for robotic manipulation with asynchronous off-policy updates. *ICRA*.
- Ha, D., & Schmidhuber, J. (2018). Recurrent world models facilitate policy evolution. *NeurIPS*.
- Hausman, K., et al. (2018). Learning an embedding space for transferable robot skills. *ICLR*.
- Houthooft, R., et al. (2016). Curiosity-driven exploration in deep reinforcement learning via Bayesian neural networks. *arXiv:1605.09674*.
- Klyubin, A. S., Polani, D., & Nehaniv, C. L. (2005). Empowerment: A universal agent-centric measure of control. *IEEE CEC*.
- Kumar, V., Todorov, E., & Levine, S. (2016). Optimal control with learned local models: Application to dexterous manipulation. *ICRA*.
- Levine, S., et al. (2016). End-to-end training of deep visuomotor policies. *JMLR*.
- Mnih, V., et al. (2013). Playing Atari with deep reinforcement learning. *arXiv:1312.5602*.
- Mohamed, S., & Rezende, D. J. (2015). Variational information maximisation for intrinsically motivated reinforcement learning. *NeurIPS*.
- Nachum, O., et al. (2018). Data-efficient hierarchical reinforcement learning. *NeurIPS*.
- Nagabandi, A., et al. (2018). Neural network dynamics for model-based deep reinforcement learning with model-free fine-tuning. *ICRA*.
- Oudeyer, P.-Y., & Kaplan, F. (2009). What is intrinsic motivation? A typology of computational approaches. *Frontiers in Neurorobotics*.
- Pathak, D., et al. (2017). Curiosity-driven exploration by self-supervised prediction. *ICML*.
- Schulman, J., et al. (2015). Trust region policy optimization. *ICML*.
- Silver, D., et al. (2016). Mastering the game of Go with deep neural networks and tree search. *Nature*.
- Sutton, R. S., Precup, D., & Singh, S. (1999). Between MDPs and semi-MDPs: A framework for temporal abstraction in reinforcement learning. *Artificial Intelligence*.
- Todorov, E., Erez, T., & Tassa, Y. (2012). MuJoCo: A physics engine for model-based control. *IROS*.
- Vezhnevets, A. S., et al. (2017). Feudal networks for hierarchical reinforcement learning. *ICML*.
- Williams, G., et al. (2016). Aggressive driving with model predictive path integral control. *ICRA*.