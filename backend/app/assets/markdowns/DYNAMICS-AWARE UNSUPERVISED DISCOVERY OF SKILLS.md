# DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS

## Abstract

Conventionally, model-based reinforcement learning (MBRL) aims to learn a global model for the dynamics of the environment. A good model can potentially enable planning algorithms to generate a large variety of behaviors and solve diverse tasks. However, learning an accurate model for complex dynamical systems is difficult, and even then, the model might not generalize well outside the distribution of states on which it was trained. In this work, we combine model-based learning with model-free learning of primitives that make model-based planning easy. To that end, we aim to answer the question: how can we discover skills whose outcomes are easy to predict? We propose an unsupervised learning algorithm, Dynamics-Aware Discovery of Skills (DADS), which simultaneously discovers _predictable_ behaviors and learns their dynamics. Our method can leverage continuous skill spaces, theoretically allowing us to learn infinitely many behaviors even for high-dimensional state-spaces. We demonstrate that _zero-shot planning_ in the learned latent space significantly outperforms standard MBRL and model-free goal-conditioned RL, can handle sparse-reward tasks, and substantially improves over prior hierarchical RL methods for unsupervised skill discovery. We have open-sourced our implementation at: [https://github.com/google-research/dads](https://github.com/google-research/dads)

![Figure 1: A humanoid agent discovers diverse locomotion primitives without any reward using DADS. We show zero-shot generalization to downstream tasks by composing the learned primitives using model predictive control, enabling the agent to follow an online sequence of goals (green markers) without any additional training.](/static/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-0-0.png)

## Introduction

Deep reinforcement learning (RL) enables autonomous learning of diverse and complex tasks with rich sensory inputs, temporally extended goals, and challenging dynamics, such as discrete game-playing domains (Mnih et al., 2013; Silver et al., 2016), and continuous control domains including locomotion (Schulman et al., 2015; Heess et al., 2017) and manipulation (Rajeswaran et al., 2017; Kalashnikov et al., 2018; Gu et al., 2017). Most deep RL approaches learn a Q-function or a policy that are directly optimized for the training task, which limits their generalization to new scenarios. In contrast, MBRL methods (Li & Todorov, 2004; Deisenroth & Rasmussen, 2011; Watter et al., 2015) can acquire dynamics models that may be utilized to perform unseen tasks at test time. While this capability has been demonstrated in some recent works (Levine et al., 2016; Nagabandi et al., 2018; Chua et al., 2018b; Kurutach et al., 2018; Ha & Schmidhuber, 2018), learning an accurate global model that works for all state-action pairs can be exceedingly challenging, especially for high-dimensional systems with complex and discontinuous dynamics.

The problem is further exacerbated as the learned global model has limited generalization outside of the state distribution it was trained on, and exploring the whole state space is generally infeasible. Can we retain the flexibility of model-based RL, while using model-free RL to acquire proficient low-level behaviors under complex dynamics?

While learning a global dynamics model that captures all the different behaviors for the entire state-space can be extremely challenging, learning a model for a specific behavior that acts only in a small part of the state-space can be much easier. For example, consider learning a model for dynamics of all gaits of a quadruped versus a model which only works for a specific gait. If we can learn many such behaviors and their corresponding dynamics, we can leverage model-predictive control to plan in the _behavior space_, as opposed to planning in the action space. The question then becomes: how do we acquire such behaviors, considering that behaviors could be random and unpredictable? To this end, we propose _Dynamics-Aware Discovery of Skills_ (DADS), an unsupervised RL framework for learning low-level skills using model-free RL with the explicit aim of making model-based control easy. Skills obtained using DADS are directly optimized for _predictability_, providing a better representation on top of which predictive models can be learned. Crucially, the skills do not require any supervision to learn, and are acquired entirely through autonomous exploration. This means that the repertoire of skills and their predictive model are learned before the agent has been tasked with any goal or reward function. When a task is provided at test-time, the agent utilizes the previously learned skills and model to immediately perform the task without any further training.

The key contribution of our work is an unsupervised reinforcement learning algorithm, DADS, grounded in mutual-information-based exploration. We demonstrate that our objective can embed learned primitives in continuous spaces, which allows us to learn a large, diverse set of skills. Crucially, our algorithm also learns to model the dynamics of the skills, which enables the use of model-based planning algorithms for downstream tasks. We adapt the conventional model predictive control algorithms to plan in the space of primitives, and demonstrate that we can compose the learned primitives to solve downstream tasks without any additional training.

## Related Work

Central to our method is the concept of skill discovery via mutual information maximization. This principle, proposed in prior work that utilized purely model-free unsupervised RL methods (Daniel et al., 2012; Florensa et al., 2017; Eysenbach et al., 2018; Gregor et al., 2016; Warde-Farley et al., 2018; Thomas et al., 2018), aims to learn diverse skills via a discriminability objective: a good set of skills is one where it is easy to distinguish the skills from each other, which means they perform distinct tasks and cover the space of possible behaviors. Building on this prior work, we distinguish our skills based on how they modify the original uncontrolled dynamics of the system. This simultaneously encourages the skills to be both _diverse_ and _predictable_. We also demonstrate that constraining the skills to be predictable makes them more amenable for hierarchical composition and thus, more useful on downstream tasks.

Another line of work that is conceptually close to our method copes with intrinsic motivation (Oudeyer & Kaplan, 2009; Oudeyer et al., 2007; Schmidhuber, 2010) which is used to drive the agent’s exploration. Examples of such works include empowerment (Klyubin et al., 2005; Mohamed & Rezende, 2015), count-based exploration (Bellemare et al., 2016; Oh et al., 2015; Tang et al., 2017; Fu et al., 2017), information gain about agent’s dynamics (Stadie et al., 2015) and forward-inverse dynamics models (Pathak et al., 2017). While our method uses an information-theoretic objective that is similar to these approaches, it is used to learn a variety of skills that can be directly used for model-based planning, which is in contrast to learning a better exploration policy for a single skill.

The skills discovered using our approach can also provide extended actions and temporal abstraction, which enable more efficient exploration for the agent to solve various tasks, reminiscent of hierarchical RL (HRL) approaches. This ranges from the classic option-critic architecture (Sutton et al., 1999; Stolle & Precup, 2002; Perkins et al., 1999) to some of the more recent work (Bacon et al., 2017; Vezhnevets et al., 2017; Nachum et al., 2018; Hausman et al., 2018). However, in contrast to end-to-end HRL approaches (Heess et al., 2016; Peng et al., 2017), we can leverage a stable, two-phase learning setup. The primitives learned through our method provide action and temporal abstraction, while planning with skill-dynamics enables hierarchical composition of these primitives, bypassing many problems of end-to-end HRL.

In the second phase of our approach, we use the learned skill-transition dynamics models to perform model-based planning - an idea that has been explored numerous times in the literature. Model-based reinforcement learning has been traditionally approached with methods that are well-suited for low-data regimes such as Gaussian Processes (Rasmussen, 2003) showing significant data-efficiency gains over model-free approaches (Deisenroth et al., 2013; Kamthe & Deisenroth, 2017; Kocijan et al., 2004; Ko et al., 2007). More recently, due to the challenges of applying these methods to high-dimensional state spaces, MBRL approaches employ Bayesian deep neural networks (Nagabandi et al., 2018; Chua et al., 2018b; Gal et al., 2016; Fu et al., 2016; Lenz et al., 2015) to learn dynamics models. In our approach, we take advantage of the deep dynamics models that are conditioned on the skill being executed, simplifying the modeling problem. In addition, the skills themselves are being learned with the objective of being predictable, further assisting with the learning of the dynamics model. There also have been multiple approaches addressing the planning component of MBRL including linear controllers for local models (Levine et al., 2016; Kumar et al., 2016; Chebotar et al., 2017), uncertainty-aware (Chua et al., 2018b; Gal et al., 2016) or deterministic planners (Nagabandi et al., 2018) and stochastic optimization methods (Williams et al., 2016). The main contribution of our work lies in discovering model-based skill primitives that can be further combined by a standard model-based planner, therefore we take advantage of an existing planning approach - Model Predictive Path Integral (Williams et al., 2016) that can leverage our pre-trained setting.

## Method

### Dynamics-Aware Discovery of Skills (DADS)

**Algorithm 1:** Dynamics-Aware Discovery of Skills (DADS)

Initialize _π, qφ_;
**while** _not converged_ **do**

Sample a skill _z_ _∼_ _p_ ( _z_ ) every episode;
Collect new _M_ on-policy samples;
Update _qφ_ using _K_ 1 steps of gradient descent on _M_ transitions;
Compute _rz_ ( _s, a, s_ _[′]_ ) for _M_ transitions;
Update _π_ using any RL algorithm;
**end**

![Figure 2: The agent _π_ interacts with the environment to produce a transition _s_ _→_ _s_ _[′]_ . Intrinsic reward is computed by computing the transition probability under _q_ for the current skill _z_, compared to random samples from the prior _p_ ( _z_ ). The agent maximizes the intrinsic reward computed for a batch of episodes, while _q_ maximizes the log-probability of the actual transitions of ( _s, z_ ) _→_ _s_ _[′]_ .](/app/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-2-0.png)

We use the information theoretic paradigm of mutual information to obtain our unsupervised skill discovery algorithm. In particular, we propose to maximize the mutual information between the next state _s_ _[′]_ and current skill _z_ conditioned on the current state _s_.

_I_ ( _s_ _[′]_ ; _z_ _| s_ ) = _H_ ( _z_ _| s_ ) _−H_ ( _z_ _| s_ _[′]_ _, s_ ) (1)

= _H_ ( _s_ _[′]_ _| s_ ) _−H_ ( _s_ _[′]_ _| s, z_ ) (2)

Mutual information in Equation 1 quantifies how much can be known about _s_ _[′]_ given _z_ and _s_, or symmetrically, _z_ given the transition from _s_ _→_ _s_ _[′]_ . From Equation 2, maximizing this objective corresponds to maximizing the diversity of transitions produced in the environment, that is denoted by the entropy _H_ ( _s_ _[′]_ _|_ _s_ ), while making _z_ informative about the next state _s_ _[′]_ by minimizing the entropy _H_ ( _s_ _[′]_ _|_ _s, z_ ). Intuitively, skills _z_ can be interpreted as abstracted action sequences which are identifiable by the transitions generated in the environment (and not just by the current state). Thus, optimizing this mutual information can be understood as encoding a diverse set of skills in the latent space _Z_, while making the transitions for a given _z_ _∈Z_ predictable. We use the entropy decomposition in Equation 2 to connect this objective with model-based control.

We want to optimize the our skill-conditioned controller _π_ ( _a_ _|_ _s, z_ ) such that the latent space _z_ _∼_ _p_ ( _z_ ) is maximally informative about the transitions _s →_ _s_ _[′]_ . Using the definition of conditional mutual information, we can rewrite Equation 2 as:

              - _[|][ s, z]_ [)]
_I_ ( _s_ _[′]_ ; _z_ _| s_ ) = _p_ ( _z, s, s_ _[′]_ ) log _[p]_ [(] _[s][′]_ (3)

_p_ ( _s_ _[′]_ _| s_ ) _[ds][′][dsdz]_

We assume the following generative model: _p_ ( _z, s, s_ _[′]_ ) = _p_ ( _z_ ) _p_ ( _s_ _|_ _z_ ) _p_ ( _s_ _[′]_ _|_ _s, z_ ), where _p_ ( _z_ ) is a user-specified prior over _Z_, _p_ ( _s|z_ ) denotes the stationary state-distribution induced by _π_ ( _a_ _|_ _s, z_ ) for a skill _z_ and _p_ ( _s_ _[′]_ _|_ _s, z_ ) denotes the transition distribution under skill _z_. Note, _p_ ( _s_ _[′]_ _|_ _s, z_ ) =

- _p_ ( _s_ _[′]_ _| s, a_ ) _π_ ( _a | s, z_ ) _da_ is intractable to compute because the underlying dynamics are unknown. However, we can variationally lower bound the objective as follows:

          - _[|][ s, z]_ [)]
_I_ ( _s_ _[′]_ ; _z_ _| s_ ) = E _z,s,s′∼p_ log _[p]_ [(] _[s][′]_

_p_ ( _s_ _[′]_ _| s_ )

     - _[|][ s, z]_ [)]
= E _z,s,s′∼p_ log _[q][φ]_ [(] _[s][′]_

_p_ ( _s_ _[′]_ _| s_ )

     - _[|][ s, z]_ [)]
= E _z,s,s′∼p_ log _[q][φ]_ [(] _[s][′]_

_p_ ( _s_ _[′]_ _| s_ )

     - _[|][ s, z]_ [)]
_≥_ E _z,s,s′∼p_ log _[q][φ]_ [(] _[s][′]_

_p_ ( _s_ _[′]_ _| s_ )

     - _[|][ s, z]_ [)]
_≥_ E _z,s,s′∼p_ log _[q][φ]_ [(] _[s][′]_

     - _[|][ s, z]_ [)]
_≥_ E _z,s,s′∼p_ log _[q][φ]_ [(] _[s][′]_

- - + E _s,z∼p_ _DKL_ ( _p_ ( _s_ _[′]_ _| s, z_ ) _|| qφ_ ( _s_ _[′]_ _| s, z_ ))

(4)

where we have used the non-negativity of KL-divergence, that is _DKL_ _≥_ 0. Note, skill-dynamics _qφ_ represents the variational approximation for the transition function _p_ ( _s_ _[′]_ _|_ _s, z_ ), which enables model-based control as described in Section 4. Equation 4 suggests an alternating optimization between _qφ_ and _π_, summarized in Algorithm 1. In every iteration:
( _Tighten_ _variational_ _lower_ _bound_ ) We minimize _DKL_ ( _p_ ( _s_ _[′]_ _|_ _s, z_ ) _||_ _qφ_ ( _s_ _[′]_ _|_ _s, z_ )) with respect to the parameters _φ_ on _z, s_ _∼_ _p_ to tighten the lower bound. For general function approximators like neural networks, we can write the gradient for _φ_ as follows:

                        - _[|][ s, z]_ [)]
_∇φ_ E _s,z_ [ _DKL_ ( _p_ ( _s_ _[′]_ _| s, z_ ) _|| qφ_ ( _s_ _[′]_ _| s, z_ ))] = _∇φ_ E _z,s,s′_ log _[p]_ [(] _[s][′]_

_qφ_ ( _s_ _[′]_ _| s, z_ )

                            -                             = _−_ E _z,s,s′_ _∇φ_ log _qφ_ ( _s_ _[′]_ _| s, z_ ) (5)

which corresponds to maximizing the likelihood of the samples from _p_ under _qφ_.

( _Maximize_ _approximate_ _lower_ _bound_ ) After fitting _qφ_, we can optimize _π_ to maximize E _z,s,s′_ [log _qφ_ ( _s_ _[′]_ _|_ _s, z_ ) _−_ log _p_ ( _s_ _[′]_ _|_ _s_ )]. Note, this is a reinforcement-learning style optimization with a reward function log _qφ_ ( _s_ _[′]_ _|_ _s, z_ ) _−_ log _p_ ( _s_ _[′]_ _|_ _s_ ). However, log _p_ ( _s_ _[′]_ _|_ _s_ ) is intractable to compute, so we approximate the reward function for _π_ :

_qφ_ ( _s_ _[′]_ _| s, z_ )
_rz_ ( _s, a, s_ _[′]_ ) = log          - _Li_ =1 _[q][φ]_ [(] _[s][′]_ _[|][ s, z][i]_ [)] + log _L,_ _zi_ _∼_ _p_ ( _z_ ) _._ (6)

The approximation is motivated as follows: _p_ ( _s_ _[′]_ _|_ _s_ ) = - _p_ ( _s_ _[′]_ _|_ _s, z_ ) _p_ ( _z|s_ ) _dz_ _≈_ - _qφ_ ( _s_ _[′]_ _|_
_s, z_ ) _p_ ( _z_ ) _dz_ _≈_ _L_ [1] - _Li_ =1 _[q][φ]_ [(] _[s][′]_ _[|]_ _[s, z][i]_ [)][ for] _[ z][i]_ _[∼]_ _[p]_ [(] _[z]_ [)][,] [where] _[ L]_ [ denotes the number of samples from]

the prior. We are using the marginal of variational approximation _qφ_ over the prior _p_ ( _z_ ) to approximate the marginal distribution of transitions. We discuss this approximation in Appendix C. Note, the final reward function _rz_ encourages the policy _π_ to produce transitions that are (a) predictable under _qφ_ ( _predictability_ ) and (b) different from the transitions produced under _zi_ _∼_ _p_ ( _z_ ) ( _diversity_ ).

To generate samples from _p_ ( _z, s, s_ _[′]_ ), we use the rollouts from the current policy _π_ for multiple samples _z_ _∼_ _p_ ( _z_ ) in an episodic setting for a fixed horizon _T_. We also introduce entropy regularization for _π_ ( _a_ _|_ _s, z_ ), which encourages the policy to discover action-sequences with similar state-transitions and to be clustered under the same skill _z_, making the policy robust besides encouraging exploration (Haarnoja et al., 2018a). The use of entropy regularization can be justified from an information bottleneck perspective as discussed for Information Maximization algorithm in (Mohamed & Rezende, 2015). This is even more extensively discussed from the graphical model perspective in Appendix B, which connects unsupervised skill discovery and information bottleneck literature, while also revealing the temporal nature of skills _z_. Details corresponding to implementation and hyperparameters are discussed in Appendix A.

## Planning Using Skill Dynamics

Given the learned skills _π_ ( _a_ _|_ _s, z_ ) and their respective skill-transition dynamics _qφ_ ( _s_ _[′]_ _|s, z_ ), we can perform model-based planning in the latent space _Z_ to optimize for a reward _r_ that is given to the agent at test time. Note, that this essentially allows us to perform zero-shot planning given the unsupervised pre-training procedure described in Section 3.

In order to perform planning, we employ the model-predictive-control (MPC) paradigm Garcia et al. (1989), which in a standard setting generates a set of action plans _Pk_ = ( _ak,_ 1 _, . . . ak,H_ ) _∼_ _P_ for a planning horizon _H_. The MPC plans can be generated due to the fact that the planner is able to simulate the trajectory _τ_ ˆ _k_ = ( _sk,_ 1 _, ak,_ 1 _. . . sk,H_ +1) assuming access to the transition dynamics _p_ ˆ( _s_ _[′]_ _|_ _s, a_ ). In addition, each plan computes the reward _r_ (ˆ _τk_ ) for its trajectory according to the reward function _r_ that is provided for the test-time task. Following the MPC principle, the planner selects the best plan according to the reward function _r_ and executes its first action _a_ 1. The planning algorithm repeats this procedure for the next state iteratively until it achieves its goal.

We use a similar strategy to design an MPC planner to exploit previously-learned skill-transition dynamics _qφ_ ( _s_ _[′]_ _|_ _s, z_ ). Note that unlike conventional model-based RL, we generate a plan _Pk_ = ( _zk,_ 1 _, . . . zk,HP_ ) in the latent space _Z_ as opposed to the action space _A_ that would be used by a standard planner. Since the primitives are temporally meaningful, it is beneficial to hold a primitive for a horizon _HZ_ _>_ 1, unlike actions which are usually held for a single step. Thus, effectively, the planning horizon for our latent space planner is _H_ = _HP_ _× HZ_, enabling longer-horizon planning using fewer primitives. Similar to the standard MPC setting, the latent space planner simulates the trajectory _τ_ ˆ _k_ = ( _sk,_ 1 _, zk,_ 1 _, ak,_ 1 _, sk,_ 2 _, zk,_ 2 _, ak,_ 2 _, . . . sk,H_ +1) and computes the reward _r_ (ˆ _τk_ ). After a small number of trajectory samples, the planner selects the first latent action _z_ 1 of the best plan, executes it for _HZ_ steps in the environment, and the repeats the process until goal completion.

The latent planner _P_ maintains a distribution of latent plans, each of length _HP_. Each element in the sequence represents the distribution of the primitive to be executed at that time step. For continuous spaces, each element of the sequence can be modelled using a normal distribution, _N_ ( _µ_ 1 _,_ Σ) _, . . . N_ ( _µHP,_ Σ). We refine the planning distributions for _R_ steps, using _K_ samples of latent plans _Pk_, and compute the _rk_ for the simulated trajectory _τ_ ˆ _k_ . The update for the parameters follows that in Model Predictive Path Integral (MPPI) controller Williams et al. (2016):

exp( _γrk_ )

- _K_ _zk,i_ _∀i_ = 1 _, . . . HP_ (7)
_p_ =1 [exp(] _[γr][p]_ [)]

_µi_ =

_K_

_k_ =1

While we keep the covariance matrix of the distributions fixed, it is possible to update that as well as shown in Williams et al. (2016). We show an overview of the planning algorithm in Figure 3, and provide more implementation details in Appendix A.

![Figure 3: At test time, the planner executes simulates the transitions in environment using skill-dynamics _q_, and updates the distribution of plans according to the computed reward on the simulated trajectories. After a few updates to the plan, the first primitive is executed in the environment using the learned agent _π_ .](/static/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-5-0.png)

## Experiments

Through our experiments, we aim to demonstrate that: (a) DADS as a general purpose skill discovery algorithm can scale to high-dimensional problems; (b) discovered skills are amenable to hierarchical composition and; (c) not only is planning in the learned latent space feasible, but it is competitive to strong baselines. In Section 6.1, we provide visualizations and qualitative analysis of the skills learned using DADS. We demonstrate in Section 6.2 and Section 6.4 that optimizing the primitives for predictability renders skills more amenable to temporal composition that can be used for Hierarchical RL. We benchmark against state-of-the-art model-based RL baseline in Section 6.3, and against goal-conditioned RL in Section 6.5.

### Qualitative Analysis

![Figure 4: Skills learned on different MuJoCo environments in the OpenAI gym. DADS can discover diverse skills without any extrinsic rewards, even for problems with high-dimensional state and action spaces.](/static/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-5-1.png)

In this section, we provide a qualitative discussion of the unsupervised skills learned using DADS. We use the MuJoCo environments (Todorov et al., 2012) from the OpenAI gym as our test-bed (Brockman et al., 2016). We find that our proposed algorithm can learn diverse skills without any reward, even in problems with high-dimensional state and actuation, as illustrated in Figure 4. DADS can discover primitives for Half-Cheetah to run forward and backward with multiple different gaits, for Ant to navigate the environment using diverse locomotion primitives and for Humanoid to walk using stable locomotion primitives with diverse gaits and direction. The videos of the discovered primitives are available at: [https://sites.google.com/view/dads-skill](https://sites.google.com/view/dads-skill)

Qualitatively, we find the skills discovered by DADS to be predictable and stable, in line with implicit constraints of the proposed objective. While the Half-Cheetah will learn to run in both backward and forward directions, DADS will disincentivize skills which make Half-Cheetah flip owing to the reduced predictability on landing. Similarly, skills discovered for Ant rarely flip over, and tend to provide stable navigation primitives in the environment. This also incentivizes the Humanoid, which is characteristically prone to collapsing and extremely unstable by design, to discover gaits which are stable for sustainable locomotion.

One of the significant advantages of the proposed objective is that it is compatible with continuous skill spaces, which has not been shown in prior work on skill discovery (Eysenbach et al., 2018). Not only does this allow us to embed a large and diverse set of skills into a compact latent space, but also the smoothness of the learned space allows us to interpolate between behaviors generated in the environment. We demonstrate this on the Ant environment (Figure 5), where we learn two-dimensional continuous skill space with a uniform prior over ( _−_ 1 _,_ 1) in each dimension, and compare it to a discrete skill space with a uniform prior over 20 skills. Similar to Eysenbach et al. (2018), we restrict the observation space of the skill-dynamics _q_ to the cartesian coordinates ( _x, y_ ). We hereby call this the _x-y prior_, and discuss its role in Section 6.2.

![Figure 5: (Left, Centre) X-Y traces of Ant skills and (Right) Heatmap to visualize the learned continuous skill space. Traces demonstrate that the continuous space offers far greater diversity of skills, while the heatmap demonstrates that the learned space is smooth, as the orientation of the X-Y trace varies smoothly as a function of the skill.](/static/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-5-2.png)

In Figure 5, we project the trajectories of the learned Ant skills from both discrete and continuous spaces onto the Cartesian plane. From the traces of the skills, it is clear that the continuous latent space can generate more diverse trajectories. We demonstrate in Section 6.3, that continuous primitives are more amenable to hierarchical composition and generally perform better on downstream tasks. More importantly, we observe that the learned skill space is semantically meaningful. The heatmap in Figure 5 shows the orientation of the trajectory (with respect to the _x_ -axis) as a function of the skill _z_ _∈Z_, which varies smoothly as _z_ is varied, with explicit interpolations shown in Appendix D.

### Skill Variance Analysis

In an unsupervised skill learning setup, it is important to optimize the primitives to be diverse. However, we argue that diversity is not sufficient for the learned primitives to be useful for downstream tasks. Primitives must exhibit low-variance behavior, which enables long-horizon composition of the learned skills in a hierarchical setup. We analyze the variance of the _x_ - _y_ trajectories in the environment, where we also benchmark the variance of the primitives learned by DIAYN (Eysenbach et al., 2018). For DIAYN, we use the _x_ - _y_ prior for the skill-discriminator, which biases the discovered skills to diversify in the _x_ - _y_ space. This step was necessary for that baseline to obtain a competitive set of navigation skills. Figure 6 (Top-Left) demonstrates that DADS, which optimizes the primitives for predictability and diversity, yields significantly lower-variance primitives when compared to DIAYN, which only optimizes for diversity. This is starkly demonstrated in the plots of X-Y traces of skills learned in different setups. Skills learned by DADS show significant control over the trajectories generated in the environment, while skills from DIAYN exhibit high variance in the environment, which limits their utility for hierarchical control. This is further demonstrated quantitatively in Section 6.4.

While optimizing for predictability already significantly reduces the variance of the trajectories generated by a primitive, we find that using the _x_ - _y_ prior with DADS brings down the skill variance even further. For quantitative benchmarks in the next sections, we assume that the Ant skills are learned using an _x_ - _y_ prior on the observation space, for both DADS and DIAYN.

![Figure 6: (Top-Left) Standard deviation of Ant’s position as a function of steps in the environment, averaged over multiple skills and normalized by the norm of the position. (Top-Right to Bottom-Left Clockwise) X-Y traces of skills learned using DIAYN with _x_ - _y_ prior, DADS with _x_ - _y_ prior and DADS without x-y prior, where the same color represents trajectories resulting from the execution of the same skill _z_ in the environment. High variance skills from DIAYN offer limited utility for hierarchical control.](/static/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-7-2.png)

### Model-Based Reinforcement Learning

The key utility of learning a parametric model _qφ_ ( _s_ _[′]_ _|s, z_ ) is to take advantage of planning algorithms for downstream tasks, which can be extremely sample-efficient. In our setup, we can solve test-time tasks in zero-shot, that is _without_ _any_ _learning_ _on_ _the_ _downstream_ _task_ . We compare with the state-of-the-art model-based RL method (Chua et al., 2018a), which learns a dynamics model parameterized as _p_ ( _s_ _[′]_ _|s, a