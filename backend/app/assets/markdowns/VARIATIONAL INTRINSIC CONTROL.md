# Variational Intrinsic Control

**Authors:** Karol Gregor, Danilo Rezende, Daan Wierstra (DeepMind)
**Published:** 2016

## Abstract
This paper introduces **Variational Intrinsic Control (VIC)**, an unsupervised reinforcement learning (RL) framework for discovering the set of **intrinsic options** (behavioral primitives) available to an agent. The method maximizes the number of distinct states an agent can reliably reach, measured via **mutual information** between options and their termination states. Two algorithms are proposed:
1. **Explicit options**: Learns an embedding space of discrete or continuous options.
2. **Implicit options**: Uses the action space itself as the option space for improved scalability.

The framework provides an explicit measure of **empowerment** (an agent’s ability to influence its environment) and scales effectively with function approximation. Experiments demonstrate its applicability in grid-worlds, 3D environments, and tasks with distractors, highlighting the importance of **closed-loop policies** over open-loop alternatives.

---

## Introduction
### Key Concepts
- **Intrinsic options**: Policies with termination conditions, defined by their *consequences* (terminal states) rather than task-specific utility. The goal is to discover as many distinct options as possible, representing the agent’s **intrinsic control space**.
- **Empowerment**: A measure of an agent’s ability to influence its environment, formalized as the mutual information between options and terminal states. Unlike traditional RL, VIC focuses on *control* rather than prediction or model learning.
- **Closed-loop vs. open-loop policies**:
  - *Open-loop*: Pre-commits to a sequence of actions (e.g., action sequences in prior empowerment work). Poor in stochastic environments.
  - *Closed-loop*: Actions are conditioned on the current state, enabling robust control.

### Motivation
- **Unsupervised RL analogy**: Just as unsupervised learning (e.g., autoencoders) extracts useful data representations, VIC extracts **useful behavioral primitives** (options) for downstream tasks.
- **Empowerment vs. curiosity**: Unlike curiosity-driven methods (e.g., prediction progress), VIC prioritizes *control* over *understanding*. An agent can achieve high empowerment without a detailed world model.
- **Applications**:
  1. **Extrinsic reward tasks**: Combine intrinsic control with extrinsic rewards to bias learning toward high-reward options.
  2. **Empowerment maximization**: Agents seek states with maximal intrinsic control, a long-term autonomy objective.

### Challenges
- **Function approximation**: Training instability with neural networks due to noisy, evolving intrinsic rewards.
- **Exploration**: The option inference function (*q*) may misclassify novel states, discouraging exploration.

---

## Related Work
### Option Learning
Prior work focuses on learning a *small* set of options for specific tasks (e.g., hierarchical RL):
- **Option-critic architecture** (Bacon & Precup, 2015): Jointly learns options and policies.
- **Subgoal discovery** (McGovern & Barto, 2001; Vezhnevets et al., 2016): Identifies useful subgoals for planning.
- **Universal value functions** (Schaul et al., 2015): Generalizes across goals but assumes goals are pre-specified.

VIC differs by aiming to discover a *large* set of intrinsic options, emphasizing **representational generalization** (similar options are close in embedding space).

### Empowerment
- **Theoretical foundations** (Klyubin et al., 2005; Salge et al., 2014): Empowerment as mutual information between actions and states.
- **Algorithmic advances** (Mohamed & Rezende, 2015): Variational methods for empowerment but limited to *open-loop* policies.
- **Key limitation**: Open-loop empowerment underestimates control in stochastic environments (e.g., an agent committing to a fixed action sequence may fail if perturbed).

### Intrinsic Motivation
- **Curiosity-driven RL** (Schmidhuber, 1991; Bellemare et al., 2016): Maximizes prediction progress or novelty.
- **Contrast with VIC**: VIC focuses on *control* (reaching distinct states) rather than *prediction* (modeling dynamics).

---

## Method
### Core Objective
Maximize the **mutual information** *I*(Ω, *s<sub>f</sub>* | *s<sub>0</sub>*) between options Ω and terminal states *s<sub>f</sub>*, given an initial state *s<sub>0</sub>*:
- **Entropy term** (*H*(*s<sub>f</sub>*|*s<sub>0</sub>*)): Encourages diversity in terminal states.
- **Conditional entropy term**: Ensures options lead to *distinct* terminal states (i.e., Ω can be inferred from *s<sub>f</sub>*).

### Variational Bound
The mutual information is intractable to compute directly. Instead, VIC optimizes a **variational lower bound** (*I<sub>VB</sub>*) using an inference function *q*(Ω | *s<sub>0</sub>*, *s<sub>f</sub>*):
```
I_VB(Ω, s_f | s_0) = − E_{p_C(Ω|s_0)}[log p_C(Ω|s_0)] + E_{p_J(s_f|s_0,Ω) p_C(Ω|s_0)}[log q(Ω|s_0, s_f)]
```
- *p<sub>C</sub>(Ω|s<sub>0</sub>)*: **Controllability prior** (distribution over options).
- *p<sub>J</sub>(s<sub>f</sub>|s<sub>0</sub>,Ω)*: Terminal state distribution induced by policy *π(a|s,Ω)*.
- *q(Ω|s<sub>0</sub>,s<sub>f</sub>)*: **Option inference function** (trains to predict Ω from *s<sub>f</sub>*).

### Intrinsic Reward
The **intrinsic reward** *r<sub>I</sub>* for an option Ω is derived from the variational bound:
```
r_I = log q(Ω|s_0, s_f) − log p_C(Ω|s_0)
```
- Intuition: *r<sub>I</sub>* measures how well Ω can be inferred from *s<sub>f</sub>* (high *r<sub>I</sub>* → distinct option).
- **Empowerment estimate**: The expected *r<sub>I</sub>* in a state *s<sub>0</sub>* approximates the logarithm of the number of reliably reachable states.

---

## Experiments & Results

### 1. Explicit Options
#### Grid World (Figure 1)
- **Task**: 2D grid with noisy actions (20% chance of random movement).
- **Options**: 30 discrete options, uniform prior *p<sub>C</sub>*.
- **Result**: Options learn to navigate to distinct, localized regions (visualized via *q*(Ω|*s<sub>f</sub>*)).
  ![Figure 1: Learned options in a grid world. Each square shows the probability of predicting an option at different locations (intensity = probability). Options navigate to distinct regions.](/app/app/assets/pages/VARIATIONAL INTRINSIC CONTROL_images/tmp61m_yc_u.pdf-5-0.png)

#### "Dangerous" Grid World (Figure 2)
- **Task**: Grid with checkerboard cells where invalid actions teleport the agent to a "trap" state.
- **Open-loop vs. closed-loop**:
  - Open-loop empowerment decreases with option length (agent prefers "safe" corridor).
  - Closed-loop empowerment grows quadratically (agent learns to navigate the dangerous area).
  ![Figure 2: Left: Environment layout with trap states (red arrows). Right: Closed-loop options learn to navigate the dangerous area. Bottom: Open-loop empowerment decreases with option length.](/app/app/assets/pages/VARIATIONAL INTRINSIC CONTROL_images/tmp61m_yc_u.pdf-4-0.png)

#### Challenges
- **Function approximation**: Struggles with neural networks due to noisy rewards. Partial fix: Freeze *q* or *π* during training.
- **Exploration**: *q* may misclassify novel states, discouraging exploration.

---

### 2. Implicit Options
#### Algorithm
- **Key idea**: Use the **action space** as the option space (simplifies inference).
- **Policies**:
  - *π<sub>p</sub>(a<sub>t</sub>|s<sub>t</sub>)*: "Generator" policy (explores).
  - *π<sub>q</sub>(a<sub>t</sub>|s<sub>t</sub>,x<sub>f</sub>)*: "Inference" policy (predicts actions from terminal observation *x<sub>f</sub>*).
- **Intrinsic reward**:
  ```
  r_I = Σ_t [log π_q(a_t|s_t) − log π_p(a_t|s_t)]
  ```
- **Exploration**: Random actions are added to the replay buffer to improve *π<sub>q</sub>*’s robustness.

#### Four-Room Grid World (Figure 3)
- **Task**: 25×25 grid with 4 rooms connected by narrow doors.
- **Result**:
  - Trajectories span multiple rooms, passing through doors efficiently.
  - Terminal state distribution is nearly uniform over reachable states.
  - **Empowerment**: 6.0 nats (≈403 reachable states).
  ![Figure 3: Left: Trajectories (blue→green) span multiple rooms. Center: Terminal state distributions are uniform. Right: 3D environment trajectories.](/app/app/assets/pages/VARIATIONAL INTRINSIC CONTROL_images/tmp61m_yc_u.pdf-8-0.png)

#### 3D Simulated Environment
- **Task**: Agent observes 40×40 RGB images, learns to navigate.
- **Result**: Trajectories are coherent (e.g., consistent rotation/movement).
- **Empowerment**: 5.4 nats (≈221 states).

#### Block-Pushing Task (Figure 4)
- **Task**: 6×6 grid with movable blocks. Agent learns to push blocks to distinct locations.
- **Result**:
  - Trajectories show sequential block manipulation (e.g., push block A down, then block B up).
  - **Empowerment**: 7.1 nats (≈1200 states).
  ![Figure 4: Left: Agent (green) pushes blocks (blue) in a sequence. Right: Empowerment grows as the agent learns to control blocks.](/app/app/assets/pages/VARIATIONAL INTRINSIC CONTROL_images/tmp61m_yc_u.pdf-8-1.png)

#### Distractors and Partial Observability
- **MNIST Digits Task**:
  - **Environment**: Pairs of MNIST digits. Agent controls digit classes (5 actions: no-op, ±class for each digit).
  - **Challenge**: Visually complex (60k×60k possible states) but only 100 controllable states (class pairs).
  - **Result**: Achieves 4.6 nats (≈99.5 states), near the theoretical maximum.
  ![Figure 5: Left: Agent learns to navigate digit classes (e.g., increment/decrement). Right: Extrinsic reward learning curves with/without unsupervised pretraining.](/app/app/assets/pages/VARIATIONAL INTRINSIC CONTROL_images/tmp61m_yc_u.pdf-8-3.png)
- **Grid World with Distractors**:
  - **Task**: Two random distractors move in the environment but do not affect the agent.
  - **Result**: Empowerment is identical with/without distractors (agent ignores irrelevant features).
  ![Figure 6: Empowerment is unaffected by distractors across environment sizes and option lengths.](/app/app/assets/pages/VARIATIONAL INTRINSIC CONTROL_images/tmp61m_yc_u.pdf-14-0.png)

#### Open vs. Closed Loop (Table 1)
- **Task**: Grid worlds with action noise (agent is randomly pushed after each step).
- **Result**: Closed-loop empowerment scales quadratically with option length, while open-loop collapses.
  ![Table 1: Closed-loop agents achieve exponentially higher empowerment across environments.](/app/app/assets/pages/VARIATIONAL INTRINSIC CONTROL_images/tmp61m_yc_u.pdf-9-0.png)

#### Extrinsic Reward Transfer (Figure 5)
- **Task**: After unsupervised pretraining, the agent is given an extrinsic reward (e.g., reach a specific location).
- **Result**: Pretrained agents learn to maximize extrinsic reward **faster** than agents trained from scratch.

---

## Conclusion
### Key Contributions
1. **Framework**: Formalizes intrinsic control as mutual information maximization between options and terminal states.
2. **Algorithms**:
   - **Explicit options**: Works for discrete/continuous option spaces but struggles with function approximation.
   - **Implicit options**: Scales better by using the action space as the option space.
3. **Empowerment**: Provides a practical estimate of empowerment, useful for autonomous agents.
4. **Closed-loop advantage**: Demonstrates superior performance over open-loop methods in stochastic environments.
5. **Transfer learning**: Unsupervised pretraining accelerates extrinsic reward learning.

### Limitations & Future Work
- **Exploration**: Current methods may fail to discover novel states due to *q*’s initial poor performance in unexplored regions.
- **State vs. observation**: Algorithms use observations (*x<sub>f</sub>*) instead of latent states (*s<sub>f</sub>*); extending to state-based empowerment is needed.
- **Hierarchical control**: Combining VIC with hierarchical RL (e.g., option-critic) could enable multi-level abstraction.

---

## References
- Arimoto, S. (1972). An algorithm for computing the capacity of arbitrary discrete memoryless channels. *IEEE Transactions on Information Theory*.
- Bacon, P.-L., & Precup, D. (2015). The option-critic architecture. *NIPS Deep RL Workshop*.
- Bellemare, M. G., et al. (2016). Unifying count-based exploration and intrinsic motivation. *arXiv:1606.01868*.
- Blahut, R. (1972). Computation of channel capacity and rate-distortion functions. *IEEE Transactions on Information Theory*.
- Goodfellow, I., Bengio, Y., & Courville, A. (2016). *Deep Learning*. MIT Press.
- Hochreiter, S., & Schmidhuber, J. (1997). Long short-term memory. *Neural Computation*.
- Klyubin, A. S., et al. (2005). Empowerment: A universal agent-centric measure of control. *IEEE Congress on Evolutionary Computation*.
- Mohamed, S., & Rezende, D. J. (2015). Variational information maximisation for intrinsically motivated reinforcement learning. *NeurIPS*.
- Mnih, V., et al. (2015). Human-level control through deep reinforcement learning. *Nature*.
- Salge, C., et al. (2014). Empowerment—an introduction. *Guided Self-Organization*.
- Schaul, T., et al. (2015). Universal value function approximators. *ICML*.
- Schmidhuber, J. (1991). Curious model-building control systems. *IEEE IJCNN*.
- Sutton, R. S., & Barto, A. G. (1998). *Reinforcement Learning: An Introduction*. MIT Press.
- Vezhnevets, A., et al. (2016). Strategic attentive writer for learning macro-actions. *arXiv:1606.04695*.
- Watkins, C. J. C. H. (1989). *Learning from Delayed Rewards*. PhD thesis, University of Cambridge.
- Williams, R. J. (1992). Simple statistical gradient-following algorithms for connectionist reinforcement learning. *Machine Learning*.