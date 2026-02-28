Published as a conference paper at ICLR 2020

## DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS


**Archit Sharma** _[∗]_ **, Shixiang Gu, Sergey Levine, Vikash Kumar, Karol Hausman**
Google Brain
_{_ architsh,shanegu,slevine,vikashplus,karolhausman _}_ @google.com


## ABSTRACT


Conventionally, model-based reinforcement learning (MBRL) aims to learn a
global model for the dynamics of the environment. A good model can potentially enable planning algorithms to generate a large variety of behaviors and
solve diverse tasks. However, learning an accurate model for complex dynamical systems is difficult, and even then, the model might not generalize well outside the distribution of states on which it was trained. In this work, we combine
model-based learning with model-free learning of primitives that make modelbased planning easy. To that end, we aim to answer the question: how can we
discover skills whose outcomes are easy to predict? We propose an unsupervised learning algorithm, Dynamics-Aware Discovery of Skills (DADS), which
simultaneously discovers _predictable_ behaviors and learns their dynamics. Our
method can leverage continuous skill spaces, theoretically, allowing us to learn
infinitely many behaviors even for high-dimensional state-spaces. We demonstrate that _zero-shot_ _planning_ in the learned latent space significantly outperforms standard MBRL and model-free goal-conditioned RL, can handle sparsereward tasks, and substantially improves over prior hierarchical RL methods
for unsupervised skill discovery. We have open-sourced our implementation at:
[https://github.com/google-research/dads](https://github.com/google-research/dads)


Figure 1: A humanoid agent discovers diverse locomotion primitives _without_ _any_ _reward_ using DADS. We
show zero-shot generalization to downstream tasks by composing the learned primitives using model predictive control, enabling the agent to follow an online sequence of goals (green markers) without any additional
training.


## 1 INTRODUCTION


Deep reinforcement learning (RL) enables autonomous learning of diverse and complex tasks with
rich sensory inputs, temporally extended goals, and challenging dynamics, such as discrete gameplaying domains (Mnih et al., 2013; Silver et al., 2016), and continuous control domains including
locomotion (Schulman et al., 2015; Heess et al., 2017) and manipulation (Rajeswaran et al., 2017;
Kalashnikov et al., 2018; Gu et al., 2017). Most of the deep RL approaches learn a Q-function
or a policy that are directly optimized for the training task, which limits their generalization to
new scenarios. In contrast, MBRL methods (Li & Todorov, 2004; Deisenroth & Rasmussen, 2011;
Watter et al., 2015) can acquire dynamics models that may be utilized to perform unseen tasks
at test time. While this capability has been demonstrated in some of the recent works (Levine
et al., 2016; Nagabandi et al., 2018; Chua et al., 2018b; Kurutach et al., 2018; Ha & Schmidhuber,


_∗_ Work done a part of the Google AI Residency program.


1



![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-0-0.png)
Published as a conference paper at ICLR 2020


2018), learning an accurate global model that works for all state-action pairs can be exceedingly
challenging, especially for high-dimensional system with complex and discontinuous dynamics.
The problem is further exacerbated as the learned global model has limited generalization outside
of the state distribution it was trained on and exploring the whole state space is generally infeasible.
Can we retain the flexibility of model-based RL, while using model-free RL to acquire proficient
low-level behaviors under complex dynamics?


While learning a global dynamics model that captures all the different behaviors for the entire statespace can be extremely challenging, learning a model for a specific behavior that acts only in a small
part of the state-space can be much easier. For example, consider learning a model for dynamics of
all gaits of a quadruped versus a model which only works for a specific gait. If we can learn many
such behaviors and their corresponding dynamics, we can leverage model-predictive control to plan
in the _behavior space_, as opposed to planning in the action space. The question then becomes: how
do we acquire such behaviors, considering that behaviors could be random and unpredictable? To
this end, we propose _Dynamics-Aware Discovery of Skills_ (DADS), an unsupervised RL framework
for learning low-level skills using model-free RL with the explicit aim of making model-based control easy. Skills obtained using DADS are directly optimized for _predictability_, providing a better
representation on top of which predictive models can be learned. Crucially, the skills do not require
any supervision to learn, and are acquired entirely through autonomous exploration. This means that
the repertoire of skills and their predictive model are learned before the agent has been tasked with
any goal or reward function. When a task is provided at test-time, the agent utilizes the previously
learned skills and model to immediately perform the task without any further training.


The key contribution of our work is an unsupervised reinforcement learning algorithm, DADS,
grounded in mutual-information-based exploration. We demonstrate that our objective can embed learned primitives in continuous spaces, which allows us to learn a large, diverse set of skills.
Crucially, our algorithm also learns to model the dynamics of the skills, which enables the use of
model-based planning algorithms for downstream tasks. We adapt the conventional model predictive control algorithms to plan in the space of primitives, and demonstrate that we can compose the
learned primitives to solve downstream tasks without any additional training.


## 2 PRELIMINARIES


Mutual information can been used as an objective to encourage exploration in reinforcement learning
(Houthooft et al., 2016; Mohamed & Rezende, 2015). According to its definition, _I_ ( _X_ ; _Y_ ) =
_H_ ( _X_ ) _−H_ ( _X_ _|_ _Y_ ), maximizing mutual information _I_ with respect to _Y_ amounts to maximizing
the entropy _H_ of _X_ while minimizing the conditional entropy _H_ ( _X_ _| Y_ ). In the context of RL, _X_ is
usually a function of the state and _Y_ a function of actions. Maximizing this objective encourages the
state entropy to be high, making the underlying policy to be exploratory. Recently, multiple works
(Eysenbach et al., 2018; Gregor et al., 2016; Achiam et al., 2018) apply this idea to learn diverse
skills which maximally cover the state space.


To leverage planning-based control, MBRL estimates the true dynamics of the environment by learning a model _p_ ˆ( _s_ _[′]_ _|_ _s, a_ ). This allows it to predict a trajectory of states _τ_ ˆ _H_ = ( _st,_ ˆ _st_ +1 _, . . ._ ˆ _st_ + _H_ )
resulting from a sequence of actions without any additional interaction with the environment. While
model-based RL methods have been demonstrated to be sample efficient compared to their modelfree counterparts, learning an effective model for the whole state-space is challenging. An openproblem in model-based RL is to incorporate temporal abstraction in model-based control, to enable
high-level planning and move-away from planning at the granular level of actions.


These seemingly unrelated ideas can be combined into a single optimization scheme, where we first
discover skills (and their models) without any extrinsic reward and then compose these skills to
optimize for the task defined at test time using model-based planning. At train time, we assume
a Markov Decision Process (MDP) _M_ 1 _≡_ ( _S, A, p_ ). The state space _S_ and action space _A_ are
assumed to be continuous, and the _A_ bounded. We assume the transition dynamics _p_ to be stochastic,
such that _p_ : _S × A × S_ _�→_ [0 _, ∞_ ). We learn a skill-conditioned policy _π_ ( _a | s, z_ ), where the skills
_z_ belongs to the space _Z_, detailed in Section 3. We assume that the skills are sampled from a prior
_p_ ( _z_ ) over _Z_ . We simultaneously learn a skill-conditioned transition function _q_ ( _s_ _[′]_ _|_ _s, z_ ), coined as
_skill-dynamics_, which predicts the transition to the next state _s_ _[′]_ from the current state _s_ for the skill
_z_ under the given dynamics _p_ . At test time, we assume an MDP _M_ 2 _≡_ ( _S, A, p, r_ ), where _S, A, p_


2


Published as a conference paper at ICLR 2020


match those defined in _M_ 1, and the reward function _r_ : _S_ _× A_ _�→_ ( _−∞, ∞_ ). We plan in _Z_ using
_q_ ( _s_ _[′]_ _| s, z_ ) to compose the learned skills _z_ for optimizing _r_ in _M_ 2, which we detail in Section 4.


3 DYNAMICS-AWARE DISCOVERY OF SKILLS (DADS)


**Algorithm 1:** Dynamics-Aware Discovery
of Skills (DADS)

Initialize _π, qφ_ ;
**while** _not converged_ **do**

Sample a skill _z_ _∼_ _p_ ( _z_ ) every episode;
Collect new _M_ on-policy samples;
Update _qφ_ using _K_ 1 steps of gradient
descent on _M_ transitions;
Compute _rz_ ( _s, a, s_ _[′]_ ) for _M_ transitions;
Update _π_ using any RL algorithm;
**end**


Figure 2: The agent _π_ interacts with the environment to produce a transition _s_ _→_ _s_ _[′]_ . Intrinsic reward is
computed by computing the transition probability under _q_ for the current skill _z_, compared to random samples
from the prior _p_ ( _z_ ). The agent maximizes the intrinsic reward computed for a batch of episodes, while _q_
maximizes the log-probability of the actual transitions of ( _s, z_ ) _→_ _s_ _[′]_ .


We use the information theoretic paradigm of mutual information to obtain our unsupervised skill
discovery algorithm. In particular, we propose to maximize the mutual information between the next
state _s_ _[′]_ and current skill _z_ conditioned on the current state _s_ .
_I_ ( _s_ _[′]_ ; _z_ _| s_ ) = _H_ ( _z_ _| s_ ) _−H_ ( _z_ _| s_ _[′]_ _, s_ ) (1)

= _H_ ( _s_ _[′]_ _| s_ ) _−H_ ( _s_ _[′]_ _| s, z_ ) (2)
Mutual information in Equation 1 quantifies how much can be known about _s_ _[′]_ given _z_ and _s_, or
symmetrically, _z_ given the transition from _s_ _→_ _s_ _[′]_ . From Equation 2, maximizing this objective
corresponds to maximizing the diversity of transitions produced in the environment, that is denoted
by the entropy _H_ ( _s_ _[′]_ _|_ _s_ ), while making _z_ informative about the next state _s_ _[′]_ by minimizing the
entropy _H_ ( _s_ _[′]_ _|_ _s, z_ ). Intuitively, skills _z_ can be interpreted as abstracted action sequences which
are identifiable by the transitions generated in the environment (and not just by the current state).
Thus, optimizing this mutual information can be understood as encoding a diverse set of skills in
the latent space _Z_, while making the transitions for a given _z_ _∈Z_ predictable. We use the entropydecomposition in Equation 2 to connect this objective with model-based control.


We want to optimize the our skill-conditioned controller _π_ ( _a_ _|_ _s, z_ ) such that the latent space
_z_ _∼_ _p_ ( _z_ ) is maximally informative about the transitions _s →_ _s_ _[′]_ . Using the definition of conditional
mutual information, we can rewrite Equation 2 as:

              - _[|][ s, z]_ [)]
_I_ ( _s_ _[′]_ ; _z_ _| s_ ) = _p_ ( _z, s, s_ _[′]_ ) log _[p]_ [(] _[s][′]_ (3)

_p_ ( _s_ _[′]_ _| s_ ) _[ds][′][dsdz]_

We assume the following generative model: _p_ ( _z, s, s_ _[′]_ ) = _p_ ( _z_ ) _p_ ( _s_ _|_ _z_ ) _p_ ( _s_ _[′]_ _|_ _s, z_ ), where _p_ ( _z_ ) is
user specified prior over _Z_, _p_ ( _s|z_ ) denotes the stationary state-distribution induced by _π_ ( _a_ _|_ _s, z_ )
for a skill _z_ and _p_ ( _s_ _[′]_ _|_ _s, z_ ) denotes the transition distribution under skill _z_ . Note, _p_ ( _s_ _[′]_ _|_ _s, z_ ) =

- _p_ ( _s_ _[′]_ _| s, a_ ) _π_ ( _a | s, z_ ) _da_ is intractable to compute because the underlying dynamics are unknown.
However, we can variationally lower bound the objective as follows:



![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-2-0.png)


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




- - + E _s,z∼p_ _DKL_ ( _p_ ( _s_ _[′]_ _| s, z_ ) _|| qφ_ ( _s_ _[′]_ _| s, z_ ))


(4)


3


Published as a conference paper at ICLR 2020


where we have used the non-negativity of KL-divergence, that is _DKL_ _≥_ 0. Note, skill-dynamics
_qφ_ represents the variational approximation for the transition function _p_ ( _s_ _[′]_ _|_ _s, z_ ), which enables
model-based control as described in Section 4. Equation 4 suggests an alternating optimization
between _qφ_ and _π_, summarized in Algorithm 1. In every iteration:
( _Tighten_ _variational_ _lower_ _bound_ ) We minimize _DKL_ ( _p_ ( _s_ _[′]_ _|_ _s, z_ ) _||_ _qφ_ ( _s_ _[′]_ _|_ _s, z_ )) with respect to
the parameters _φ_ on _z, s_ _∼_ _p_ to tighten the lower bound. For general function approximators like
neural networks, we can write the gradient for _φ_ as follows:




                        - _[|][ s, z]_ [)]
_∇φ_ E _s,z_ [ _DKL_ ( _p_ ( _s_ _[′]_ _| s, z_ ) _|| qφ_ ( _s_ _[′]_ _| s, z_ ))] = _∇φ_ E _z,s,s′_ log _[p]_ [(] _[s][′]_

_qφ_ ( _s_ _[′]_ _| s, z_ )








                            -                             = _−_ E _z,s,s′_ _∇φ_ log _qφ_ ( _s_ _[′]_ _| s, z_ ) (5)


which corresponds to maximizing the likelihood of the samples from _p_ under _qφ_ .


( _Maximize_ _approximate_ _lower_ _bound_ ) After fitting _qφ_, we can optimize _π_ to maximize
E _z,s,s′_ [log _qφ_ ( _s_ _[′]_ _|_ _s, z_ ) _−_ log _p_ ( _s_ _[′]_ _|_ _s_ )]. Note, this is a reinforcement-learning style optimization with a reward function log _qφ_ ( _s_ _[′]_ _|_ _s, z_ ) _−_ log _p_ ( _s_ _[′]_ _|_ _s_ ). However, log _p_ ( _s_ _[′]_ _|_ _s_ ) is intractable to
compute, so we approximate the reward function for _π_ :


_qφ_ ( _s_ _[′]_ _| s, z_ )
_rz_ ( _s, a, s_ _[′]_ ) = log          - _Li_ =1 _[q][φ]_ [(] _[s][′]_ _[|][ s, z][i]_ [)] + log _L,_ _zi_ _∼_ _p_ ( _z_ ) _._ (6)

The approximation is motivated as follows: _p_ ( _s_ _[′]_ _|_ _s_ ) = - _p_ ( _s_ _[′]_ _|_ _s, z_ ) _p_ ( _z|s_ ) _dz_ _≈_ - _qφ_ ( _s_ _[′]_ _|_
_s, z_ ) _p_ ( _z_ ) _dz_ _≈_ _L_ [1] - _Li_ =1 _[q][φ]_ [(] _[s][′]_ _[|]_ _[s, z][i]_ [)][ for] _[ z][i]_ _[∼]_ _[p]_ [(] _[z]_ [)][,] [where] _[ L]_ [ denotes the number of samples from]

the prior. We are using the marginal of variational approximation _qφ_ over the prior _p_ ( _z_ ) to approximate the marginal distribution of transitions. We discuss this approximation in Appendix C. Note,
the final reward function _rz_ encourages the policy _π_ to produce transitions that are (a) predictable
under _qφ_ ( _predictability_ ) and (b) different from the transitions produced under _zi_ _∼_ _p_ ( _z_ ) ( _diversity_ ).

To generate samples from _p_ ( _z, s, s_ _[′]_ ), we use the rollouts from the current policy _π_ for multiple
samples _z_ _∼_ _p_ ( _z_ ) in an episodic setting for a fixed horizon _T_ . We also introduce entropy regularization for _π_ ( _a_ _|_ _s, z_ ), which encourages the policy to discover action-sequences with similar
state-transitions and to be clustered under the same skill _z_, making the policy robust besides encouraging exploration (Haarnoja et al., 2018a). The use of entropy regularization can be justified
from an information bottleneck perspective as discussed for Information Maximization algorithm in
(Mohamed & Rezende, 2015). This is even more extensively discussed from the graphical model
perspective in Appendix B, which connects unsupervised skill discovery and information bottleneck
literature, while also revealing the temporal nature of skills _z_ . Details corresponding to implementation and hyperparameters are discussed in Appendix A.


## 4 PLANNING USING SKILL DYNAMICS


Given the learned skills _π_ ( _a_ _|_ _s, z_ ) and their respective skill-transition dynamics _qφ_ ( _s_ _[′]_ _|_ _s, z_ ), we
can perform model-based planning in the latent space _Z_ to optimize for a reward _r_ that is given to
the agent at test time. Note, that this essentially allows us to perform zero-shot planning given the
unsupervised pre-training procedure described in Section 3.


In order to perform planning, we employ the model-predictive-control (MPC) paradigm Garcia et al.
(1989), which in a standard setting generates a set of action plans _Pk_ = ( _ak,_ 1 _, . . . ak,H_ ) _∼_ _P_ for
a planning horizon _H_ . The MPC plans can be generated due to the fact that the planner is able
to simulate the trajectory _τ_ ˆ _k_ = ( _sk,_ 1 _, ak,_ 1 _. . . sk,H_ +1) assuming access to the transition dynamics
_p_ ˆ( _s_ _[′]_ _|_ _s, a_ ). In addition, each plan computes the reward _r_ (ˆ _τk_ ) for its trajectory according to the
reward function _r_ that is provided for the test-time task. Following the MPC principle, the planner
selects the best plan according to the reward function _r_ and executes its first action _a_ 1. The planning
algorithm repeats this procedure for the next state iteratively until it achieves its goal.


We use a similar strategy to design an MPC planner to exploit previously-learned skill-transition
dynamics _qφ_ ( _s_ _[′]_ _|_ _s, z_ ). Note that unlike conventional model-based RL, we generate a plan _Pk_ =
( _zk,_ 1 _, . . . zk,HP_ ) in the latent space _Z_ as opposed to the action space _A_ that would be used by a
standard planner. Since the primitives are temporally meaningful, it is beneficial to hold a primitive


4


Published as a conference paper at ICLR 2020


**Algorithm 2:** Latent Space Planner


_s ←_ _s_ 0;
Initialize parameters _µ_ 1 _, . . . µHP_ ;
**for** _i ←_ 1 **to** _HE/HZ_ **do**

**for** _j_ _←_ 1 **to** _R_ **do**

_{zi, . . . zi_ + _HP −_ 1 _}_ _[K]_ _k_ =1 _[∼]_
_Ni, . . . Ni_ + _HP −_ 1 ;
Compute _renv_ for
_{zi, . . . zi_ + _HP −_ 1 _}_ _[K]_ _k_ =1 [;]
Update _µi, . . ., µi_ + _HP −_ 1;
**end**
Sample _zi_ from _Ni_ ;
Execute _π_ ( _a|s, zi_ ) for _HZ_ steps;
Initialize _µi_ + _HP_ ;
**end**


Figure 3: At test time, the planner executes simulates the transitions in environment using skill-dynamics _q_,
and updates the distribution of plans according to the computed reward on the simulated trajectories. After a
few updates to the plan, the first primitive is executed in the environment using the learned agent _π_ .


for a horizon _HZ_ _>_ 1, unlike actions which are usually held for a single step. Thus, effectively, the
planning horizon for our latent space planner is _H_ = _HP_ _× HZ_, enabling longer-horizon planning
using fewer primitives. Similar to the standard MPC setting, the latent space planner simulates the
trajectory _τ_ ˆ _k_ = ( _sk,_ 1 _, zk,_ 1 _, ak,_ 1 _, sk,_ 2 _, zk,_ 2 _, ak,_ 2 _, . . . sk,H_ +1) and computes the reward _r_ (ˆ _τk_ ). After
a small number of trajectory samples, the planner selects the first latent action _z_ 1 of the best plan,
executes it for _HZ_ steps in the environment, and the repeats the process until goal completion.


The latent planner _P_ maintains a distribution of latent plans, each of length _HP_ . Each element
in the sequence represents the distribution of the primitive to be executed at that time step. For
continuous spaces, each element of the sequence can be modelled using a normal distribution,
_N_ ( _µ_ 1 _,_ Σ) _, . . . N_ ( _µHP,_ Σ). We refine the planning distributions for _R_ steps, using _K_ samples of
latent plans _Pk_, and compute the _rk_ for the simulated trajectory _τ_ ˆ _k_ . The update for the parameters
follows that in Model Predictive Path Integral (MPPI) controller Williams et al. (2016):



![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-4-0.png)

exp( _γrk_ )

- _K_ _zk,i_ _∀i_ = 1 _, . . . HP_ (7)
_p_ =1 [exp(] _[γr][p]_ [)]



_µi_ =



_K_



_k_ =1



While we keep the covariance matrix of the distributions fixed, it is possible to update that as well
as shown in Williams et al. (2016). We show an overview of the planning algorithm in Figure 3, and
provide more implementation details in Appendix A.


## 5 RELATED WORK


Central to our method is the concept of skill discovery via mutual information maximization. This
principle, proposed in prior work that utilized purely model-free unsupervised RL methods (Daniel
et al., 2012; Florensa et al., 2017; Eysenbach et al., 2018; Gregor et al., 2016; Warde-Farley et al.,
2018; Thomas et al., 2018), aims to learn diverse skills via a discriminability objective: a good
set of skills is one where it is easy to distinguish the skills from each other, which means they
perform distinct tasks and cover the space of possible behaviors. Building on this prior work, we
distinguish our skills based on how they modify the original uncontrolled dynamics of the system.
This simultaneously encourages the skills to be both _diverse_ and _predictable_ . We also demonstrate
that constraining the skills to be predictable makes them more amenable for hierarchical composition
and thus, more useful on downstream tasks.


Another line of work that is conceptually close to our method copes with intrinsic motivation (Oudeyer & Kaplan, 2009; Oudeyer et al., 2007; Schmidhuber, 2010) which is used to drive
the agent’s exploration. Examples of such works include empowerment Klyubin et al. (2005); Mohamed & Rezende (2015), count-based exploration Bellemare et al. (2016); Oh et al. (2015); Tang
et al. (2017); Fu et al. (2017), information gain about agent’s dynamics Stadie et al. (2015) and


5


Published as a conference paper at ICLR 2020


forward-inverse dynamics models Pathak et al. (2017). While our method uses an informationtheoretic objective that is similar to these approaches, it is used to learn a variety of skills that can be
directly used for model-based planning, which is in contrast to learning a better exploration policy
for a single skill.


The skills discovered using our approach can also provide extended actions and temporal abstraction, which enable more efficient exploration for the agent to solve various tasks, reminiscent of
hierarchical RL (HRL) approaches. This ranges from the classic option-critic architecture (Sutton
et al., 1999; Stolle & Precup, 2002; Perkins et al., 1999) to some of the more recent work (Bacon
et al., 2017; Vezhnevets et al., 2017; Nachum et al., 2018; Hausman et al., 2018). However, in
contrast to end-to-end HRL approaches (Heess et al., 2016; Peng et al., 2017), we can leverage a
stable, two-phase learning setup. The primitives learned through our method provide action and
temporal abstraction, while planning with skill-dynamics enables hierarchical composition of these
primitives, bypassing many problems of end-to-end HRL.


In the second phase of our approach, we use the learned skill-transition dynamics models to perform
model-based planning - an idea that has been explored numerous times in the literature. Model-based
reinforcement learning has been traditionally approached with methods that are well-suited for lowdata regimes such as Gaussian Processes (Rasmussen, 2003) showing significant data-efficiency
gains over model-free approaches (Deisenroth et al., 2013; Kamthe & Deisenroth, 2017; Kocijan
et al., 2004; Ko et al., 2007). More recently, due to the challenges of applying these methods to highdimensional state spaces, MBRL approaches employs Bayesian deep neural networks (Nagabandi
et al., 2018; Chua et al., 2018b; Gal et al., 2016; Fu et al., 2016; Lenz et al., 2015) to learn dynamics
models. In our approach, we take advantage of the deep dynamics models that are conditioned
on the skill being executed, simplifying the modelling problem. In addition, the skills themselves
are being learned with the objective of being predictable, further assists with the learning of the
dynamics model. There also have been multiple approaches addressing the planning component
of MBRL including linear controllers for local models (Levine et al., 2016; Kumar et al., 2016;
Chebotar et al., 2017), uncertainty-aware (Chua et al., 2018b; Gal et al., 2016) or deterministic
planners (Nagabandi et al., 2018) and stochastic optimization methods (Williams et al., 2016). The
main contribution of our work lies in discovering model-based skill primitives that can be further
combined by a standard model-based planner, therefore we take advantage of an existing planning
approach - Model Predictive Path Integral (Williams et al., 2016) that can leverage our pre-trained
setting.


## 6 EXPERIMENTS


Through our experiments, we aim to demonstrate that: (a) DADS as a general purpose skill discovery algorithm can scale to high-dimensional problems; (b) discovered skills are amenable to
hierarchical composition and; (c) not only is planning in the learned latent space feasible, but it is
competitive to strong baselines. In Section 6.1, we provide visualizations and qualitative analysis of
the skills learned using DADS. We demonstrate in Section 6.2 and Section 6.4 that optimizing the
primitives for predictability renders skills more amenable to temporal composition that can be used
for Hierarchical RL.We benchmark against state-of-the-art model-based RL baseline in Section 6.3,
and against goal-conditioned RL in Section 6.5.


### 6.1 QUALITATIVE ANALYSIS


Figure 4: Skills learned on different MuJoCo environments in the OpenAI gym. DADS can discover diverse
skills without any extrinsic rewards, even for problems with high-dimensional state and action spaces.


6



![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-5-0.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-5-1.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-5-2.png)
Published as a conference paper at ICLR 2020


In this section, we provide a qualitative discussion of the unsupervised skills learned using DADS.
We use the MuJoCo environments (Todorov et al., 2012) from the OpenAI gym as our test-bed
(Brockman et al., 2016). We find that our proposed algorithm can learn diverse skills without any
reward, even in problems with high-dimensional state and actuation, as illustrated in Figure 4. DADS
can discover primitives for Half-Cheetah to run forward and backward with multiple different gaits,
for Ant to navigate the environment using diverse locomotion primitives and for Humanoid to walk
using stable locomotion primitives with diverse gaits and direction. The videos of the discovered
primitives are available at: [https://sites.google.com/view/dads-skill](https://sites.google.com/view/dads-skill)


Qualitatively, we find the skills discovered by DADS to be predictable and stable, in line with implicit constraints of the proposed objective. While the Half-Cheetah will learn to run in both backward and forward directions, DADS will disincentivize skills which make Half-Cheetah flip owing to
the reduced predictability on landing. Similarly, skills discovered for Ant rarely flip over, and tend
to provide stable navigation primitives in the environment. This also incentivizes the Humanoid,
which is characteristically prone to collapsing and extremely unstable by design, to discover gaits
which are stable for sustainable locomotion.


One of the significant advantages of the proposed objective is that it is compatible with continuous
skill spaces, which has not been shown in prior work on skill discovery (Eysenbach et al., 2018). Not
only does this allow us to embed a large and diverse set of skills into a compact latent space, but also
the smoothness of the learned space allows us to interpolate between behaviors generated in the environment. We demonstrate this on the Ant environment (Figure 5), where we learn two-dimensional
continuous skill space with a uniform prior over ( _−_ 1 _,_ 1) in each dimension, and compare it to a discrete skill space with a uniform prior over 20 skills. Similar to Eysenbach et al. (2018), we restrict
the observation space of the skill-dynamics _q_ to the cartesian coordinates ( _x, y_ ). We hereby call this
the _x-y prior_, and discuss its role in Section 6.2.


Figure 5: (Left, Centre) X-Y traces of Ant skills and (Right) Heatmap to visualize the learned continuous skill
space. Traces demonstrate that the continuous space offers far greater diversity of skills, while the heatmap
demonstrates that the learned space is smooth, as the orientation of the X-Y trace varies smoothly as a function
of the skill.


In Figure 5, we project the trajectories of the learned Ant skills from both discrete and continuous
spaces onto the Cartesian plane. From the traces of the skills, it is clear that the continuous latent
space can generate more diverse trajectories. We demonstrate in Section 6.3, that continuous primitives are more amenable to hierarchical composition and generally perform better on downstream
tasks. More importantly, we observe that the learned skill space is semantically meaningful. The
heatmap in Figure 5 shows the orientation of the trajectory (with respect to the _x_ -axis) as a function of the skill _z_ _∈Z_, which varies smoothly as _z_ is varied, with explicit interpolations shown in
Appendix D.


### 6.2 SKILL VARIANCE ANALYSIS


In an unsupervised skill learning setup, it is important to optimize the primitives to be diverse. However, we argue that diversity is not sufficient for the learned primitives to be useful for downstream
tasks. Primitives must exhibit low-variance behavior, which enables long-horizon composition of
the learned skills in a hierarchical setup. We analyze the variance of the _x_ - _y_ trajectories in the environment, where we also benchmark the variance of the primitives learned by DIAYN (Eysenbach
et al., 2018). For DIAYN, we use the _x_ - _y_ prior for the skill-discriminator, which biases the discovered skills to diversify in the _x_ - _y_ space. This step was necessary for that baseline to obtain a


7



![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-6-0.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-6-1.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-6-2.png)
Published as a conference paper at ICLR 2020


DADS without x-y prior



DIAYN with x-y prior


DADS with x-y prior



![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-7-0.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-7-1.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-7-2.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-7-3.png)

Figure 6: (Top-Left) Standard deviation of Ant’s position as a function of steps in the environment, averaged
over multiple skills and normalized by the norm of the position. (Top-Right to Bottom-Left Clockwise) X-Y
traces of skills learned using DIAYN with _x_ - _y_ prior, DADS with _x_ - _y_ prior and DADS without x-y prior, where
the same color represents trajectories resulting from the execution of the same skill _z_ in the environment. High
variance skills from DIAYN offer limited utility for hierarchical control.


competitive set of navigation skills. Figure 6 (Top-Left) demonstrates that DADS, which optimizes
the primitives for predictability and diversity, yields significantly lower-variance primitives when
compared to DIAYN, which only optimizes for diversity. This is starkly demonstrated in the plots
of X-Y traces of skills learned in different setups. Skills learned by DADS show significant control
over the trajectories generated in the environment, while skills from DIAYN exhibit high variance
in the environment, which limits their utility for hierarchical control. This is further demonstrated
quantitatively in Section 6.4.


While optimizing for predictability already significantly reduces the variance of the trajectories generated by a primitive, we find that using the _x_ - _y_ prior with DADS brings down the skill variance
even further. For quantitative benchmarks in the next sections, we assume that the Ant skills are
learned using an _x_ - _y_ prior on the observation space, for both DADS and DIAYN.


### 6.3 MODEL-BASED REINFORCEMENT LEARNING


The key utility of learning a parametric model _qφ_ ( _s_ _[′]_ _|s, z_ ) is to take advantage of planning algorithms
for downstream tasks, which can be extremely sample-efficient. In our setup, we can solve testtime tasks in zero-shot, that is _without_ _any_ _learning_ _on_ _the_ _downstream_ _task_ . We compare with
the state-of-the-art model-based RL method (Chua et al., 2018a), which learns a dynamics model
parameterized as _p_ ( _s_ _[′]_ _|s, a_ ), on the task of the Ant navigating to a specified goal with a dense reward.
Given a goal _g_, reward at any position _u_ is given by _r_ ( _u_ ) = _−∥g −_ _u∥_ 2. We benchmark our method
against the following variants:


_•_ Random-MBRL ( _rMBRL_ ): We train the model _p_ ( _s_ _[′]_ _|s, a_ ) on randomly collected trajectories, and test the zero-shot generalization of the model on a distribution of goals.


8


Published as a conference paper at ICLR 2020


_•_ Weak-oracle MBRL ( _WO-MBRL_ ): We train the model _p_ ( _s_ _[′]_ _|s, a_ ) on trajectories generated
by the planner to navigate to a goal, randomly sampled in every episode. The distribution
of goals during training matches the distribution at test time.

_•_ Strong-oracle MBRL ( _SO-MBRL_ ): We train the model _p_ ( _s_ _[′]_ _|s, a_ ) on a trajectories generated
by the planner to navigate to a specific goal, which is fixed for both training and test time.


Amongst the variants, only the rMBRL matches our assumptions of having an unsupervised taskagnostic training. Both WO-MBRL and SO-MBRL benefit from goal-directed exploration during training, a significant advantage over DADS, which only uses mutual-information-based exploration.

We use ∆= [�] _t_ _[H]_ =1 _H−∥rg_ ( _u∥_ )2 [as the metric, which represents the distance to the goal] _[ g]_ [ averaged over the]
episode (with the same fixed horizon _H_ for all models and experiments), normalized by the initial
distance to the goal _g_ . Therefore, lower ∆ indicates better performance and 0 _<_ ∆ _≤_ 1 (assuming
the agent goes closer to the goal). The test set of goals is fixed for all the methods, sampled from

[ _−_ 15 _,_ 15] [2] .


Figure 7 demonstrates that the zero-shot planning significantly outperforms all model-based RL
baselines, despite the advantage of the baselines being trained on the test goal(s). For the experiment depicted in Figure 7 (Right), DADS has an unsupervised pre-training phase, unlike SO-MBRL
which is training directly for the task. A comparison with Random-MBRL shows the significance of
mutual-information-based exploration, especially with the right parameterization and priors. This
experiment also demonstrates the advantage of learning a continuous space of primitives, which
outperforms planning on discrete primitives.


Figure 7: (Left) The results of the MPPI controller on skills learned using DADS-c (continuous primitives)
and DADS-d (discrete primitives) significantly outperforms state-of-the-art model-based RL. (Right) Planning
for a new task does not require any additional training and outperforms model-based RL being trained for the
specific task.


### 6.4 HIERARCHICAL CONTROL WITH UNSUPERVISED PRIMITIVES


We benchmark hierarchical control for primitives learned without supervision, against our proposed
scheme using an MPPI based planner on top of DADS-learned skills. We persist with the task of
Ant-navigation as described in 6.3. We benchmark against Hierarchical DIAYN (Eysenbach et al.,
2018), which learns the skills using the DIAYN objective, freezes the low-level policy and learns
a meta-controller that outputs the skill to be executed for the next _HZ_ steps. We provide the _x_ - _y_
prior to the DIAYN’s disciminator while learning the skills for the Ant agent. The performance
of the meta-controller is constrained by the low-level policy, however, this hierarchical scheme is
agnostic to the algorithm used to learn the low-level policy. To contrast the quality of primitives
learned by the DADS and DIAYN, we also benchmark against Hierarchical DADS, which learns a
meta-controller the same way as Hierarchical DIAYN, but learns the skills using DADS.


From Figure 8 (Left) We find that the meta-controller is unable to compose the skills learned by
DIAYN, while the same meta-controller can learn to compose skills by DADS to navigate the Ant
to different goals. This result seems to confirm our intuition described in Section 6.2, that the high
variance of the DIAYN skills limits their temporal compositionality. Interestingly, learning a RL


9



![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-8-0.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-8-1.png)
Published as a conference paper at ICLR 2020


Figure 8: (Left) A RL-trained meta-controller is unable to compose primitive learned by DIAYN to navigate
Ant to a goal, while it succeeds to do so using the primitives learned by DADS. (Right) Goal-Conditioned RL
(GCRL-dense/sparse) does not generalize outside its training distribution, while MPPI controller on learned
skills (DADS-dense/sparse) experiences significantly smaller degrade in performance.


meta-controller reaches similar performance to the MPPI controller, taking an additional 200 _,_ 000
samples per goal.


### 6.5 GOAL-CONDITIONED RL
To demonstrate the benefits of our approach over model-free RL, we benchmark against goalconditioned RL on two versions of Ant-navigation: (a) with a dense reward _r_ ( _u_ ) and (b) with a
sparse reward _r_ ( _u_ ) = 1 if _∥u −_ _g∥_ 2 _≤_ _ϵ_, else 0. We train the goal-conditioned RL agent using soft
actor-critic, where the state variable of the agent is augmented with _u −_ _g_, the position delta to the
goal. The agent gets a randomly sampled goal from [ _−_ 10 _,_ 10] [2] at the beginning of the episode.


In Figure 8 (Right), we measure the average performance of the all the methods as a function of
the initial distance of the goal, ranging from 5 to 30 metres. For dense reward navigation, we observe that while model-based planning on DADS-learned skills degrades smoothly as the initial
distance to goal to increases, goal-conditioned RL experiences a sudden deterioration outside the
goal distribution it was trained on. Even within the goal distribution observed during training of
goal-conditioned RL model, skill-space planning performs competitively to it. With sparse reward
navigation, goal-conditioned RL is unable to navigate, while MPPI demonstrates comparable performance to the dense reward up to about 20 metres. This highlights the utility of learning task-agnostic
skills, which makes them more general while showing that latent space planning can be leveraged
for tasks requiring long-horizon planning.


## 7 CONCLUSION

We have proposed a novel unsupervised skill learning algorithm that is amenable to model-based
planning for hierarchical control on downstream tasks. We show that our skill learning method can
scale to high-dimensional state-spaces, while discovering a diverse set of low-variance skills. In addition, we demonstrated that, without any training on the specified task, we can compose the learned
skills to outperform competitive model-based baselines that were trained with the knowledge of the
test tasks. We plan to extend the algorithm to work with off-policy data, potentially using relabelling
tricks (Andrychowicz et al., 2017; Nachum et al., 2018) and explore more nuanced planning algorithms. We plan to apply the hereby-introduced method to different domains, such as manipulation
and enable skill/model discovery directly from images.


## 8 ACKNOWLEDGEMENTS


We would like to thank Evan Liu, Ben Eysenbach, Anusha Nagabandi for their help in reproducing
the baselines for this work. We are thankful to Ben Eysenbach for their comments and discussion
on the initial drafts. We would also like to acknowledge Ofir Nachum, Alex Alemi, Daniel Freeman, Yiding Jiang, Allan Zhou and other colleagues at Google Brain for their helpful feedback and
discussions at various stages of this work. We are also thankful to Michael Ahn and others in Adept
team for their support, especially with the infrastructure setup and scaling up the experiments.


10



![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-9-0.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-9-1.png)
Published as a conference paper at ICLR 2020


## REFERENCES


Mart´ın Abadi, Ashish Agarwal, Paul Barham, Eugene Brevdo, Zhifeng Chen, Craig Citro, Greg S.
Corrado, Andy Davis, Jeffrey Dean, Matthieu Devin, Sanjay Ghemawat, Ian Goodfellow, Andrew
Harp, Geoffrey Irving, Michael Isard, Yangqing Jia, Rafal Jozefowicz, Lukasz Kaiser, Manjunath
Kudlur, Josh Levenberg, Dan Man´e, Rajat Monga, Sherry Moore, Derek Murray, Chris Olah,
Mike Schuster, Jonathon Shlens, Benoit Steiner, Ilya Sutskever, Kunal Talwar, Paul Tucker, Vincent Vanhoucke, Vijay Vasudevan, Fernanda Vi´egas, Oriol Vinyals, Pete Warden, Martin Wattenberg, Martin Wicke, Yuan Yu, and Xiaoqiang Zheng. TensorFlow: Large-scale machine learning
[on heterogeneous systems, 2015. URL http://tensorflow.org/. Software available from](http://tensorflow.org/)
tensorflow.org.


Joshua Achiam, Harrison Edwards, Dario Amodei, and Pieter Abbeel. Variational option discovery
algorithms. _arXiv preprint arXiv:1807.10299_, 2018.


David Barber Felix Agakov. The im algorithm: a variational approach to information maximization.
_Advances in Neural Information Processing Systems_, 16:201, 2004.


Alexander A Alemi and Ian Fischer. Therml: Thermodynamics of machine learning. _arXiv preprint_
_arXiv:1807.04162_, 2018.


Marcin Andrychowicz, Filip Wolski, Alex Ray, Jonas Schneider, Rachel Fong, Peter Welinder, Bob
McGrew, Josh Tobin, Pieter Abbeel, and Wojciech Zaremba. Hindsight experience replay. _CoRR_,
abs/1707.01495, 2017. [URL http://arxiv.org/abs/1707.01495.](http://arxiv.org/abs/1707.01495)


Pierre-Luc Bacon, Jean Harb, and Doina Precup. The option-critic architecture. In _Thirty-First AAAI_
_Conference on Artificial Intelligence_, 2017.


Marc Bellemare, Sriram Srinivasan, Georg Ostrovski, Tom Schaul, David Saxton, and Remi Munos.
Unifying count-based exploration and intrinsic motivation. In _Advances_ _in_ _Neural_ _Information_
_Processing Systems_, pp. 1471–1479, 2016.


Greg Brockman, Vicki Cheung, Ludwig Pettersson, Jonas Schneider, John Schulman, Jie Tang, and
Wojciech Zaremba. Openai gym. _CoRR_, abs/1606.01540, 2016. [URL http://arxiv.org/](http://arxiv.org/abs/1606.01540)
[abs/1606.01540.](http://arxiv.org/abs/1606.01540)


Yevgen Chebotar, Karol Hausman, Marvin Zhang, Gaurav Sukhatme, Stefan Schaal, and Sergey
Levine. Combining model-based and model-free updates for trajectory-centric reinforcement
learning. In _Proceedings of the 34th International Conference on Machine Learning-Volume 70_,
pp. 703–711. JMLR. org, 2017.


Kurtland Chua, Roberto Calandra, Rowan McAllister, and Sergey Levine. Deep reinforcement learning in a handful of trials using probabilistic dynamics models. _CoRR_, abs/1805.12114, 2018a.
[URL http://arxiv.org/abs/1805.12114.](http://arxiv.org/abs/1805.12114)


Kurtland Chua, Roberto Calandra, Rowan McAllister, and Sergey Levine. Deep reinforcement learning in a handful of trials using probabilistic dynamics models. In _Advances in Neural Information_
_Processing Systems_, pp. 4759–4770, 2018b.


Imre Csisz´ar and Frantisek Matus. Information projections revisited. _IEEE Transactions on Infor-_
_mation Theory_, 49(6):1474–1490, 2003.


Christian Daniel, Gerhard Neumann, and Jan Peters. Hierarchical relative entropy policy search. In
_Artificial Intelligence and Statistics_, pp. 273–281, 2012.


Marc Deisenroth and Carl E Rasmussen. Pilco: A model-based and data-efficient approach to policy
search. In _Proceedings of the 28th International Conference on machine learning (ICML-11)_, pp.
465–472, 2011.


Marc Peter Deisenroth, Dieter Fox, and Carl Edward Rasmussen. Gaussian processes for dataefficient learning in robotics and control. _IEEE_ _transactions_ _on_ _pattern_ _analysis_ _and_ _machine_
_intelligence_, 37(2):408–423, 2013.


11


Published as a conference paper at ICLR 2020


Benjamin Eysenbach, Abhishek Gupta, Julian Ibarz, and Sergey Levine. Diversity is all you need:
Learning skills without a reward function. _arXiv preprint arXiv:1802.06070_, 2018.


Carlos Florensa, Yan Duan, and Pieter Abbeel. Stochastic neural networks for hierarchical reinforcement learning. _arXiv preprint arXiv:1704.03012_, 2017.


Nir Friedman, Ori Mosenzon, Noam Slonim, and Naftali Tishby. Multivariate information bottleneck. In _Proceedings of the Seventeenth conference on Uncertainty in artificial intelligence_, pp.
152–161. Morgan Kaufmann Publishers Inc., 2001.


Justin Fu, Sergey Levine, and Pieter Abbeel. One-shot learning of manipulation skills with online
dynamics adaptation and neural network priors. In _2016 IEEE/RSJ International Conference on_
_Intelligent Robots and Systems (IROS)_, pp. 4019–4026. IEEE, 2016.


Justin Fu, John Co-Reyes, and Sergey Levine. Ex2: Exploration with exemplar models for
deep reinforcement learning. In I. Guyon, U. V. Luxburg, S. Bengio, H. Wallach, R. Fergus,
S. Vishwanathan, and R. Garnett (eds.), _Advances in Neural Information Processing Systems 30_,
pp. 2577–2587. Curran Associates, Inc., 2017. URL [http://papers.nips.cc/paper/](http://papers.nips.cc/paper/6851-ex2-exploration-with-exemplar-models-for-deep-reinforcement-learning.pdf)
[6851-ex2-exploration-with-exemplar-models-for-deep-reinforcement-learning.](http://papers.nips.cc/paper/6851-ex2-exploration-with-exemplar-models-for-deep-reinforcement-learning.pdf)
[pdf.](http://papers.nips.cc/paper/6851-ex2-exploration-with-exemplar-models-for-deep-reinforcement-learning.pdf)


Yarin Gal, Rowan McAllister, and Carl Edward Rasmussen. Improving pilco with bayesian neural
network dynamics models. In _Data-Efficient_ _Machine_ _Learning_ _workshop,_ _ICML_, volume 4,
2016.


Carlos E Garcia, David M Prett, and Manfred Morari. Model predictive control: theory and practicea
survey. _Automatica_, 25(3):335–348, 1989.


Karol Gregor, Danilo Jimenez Rezende, and Daan Wierstra. Variational intrinsic control. _arXiv_
_preprint arXiv:1611.07507_, 2016.


Shixiang Gu, Ethan Holly, Timothy Lillicrap, and Sergey Levine. Deep reinforcement learning for
robotic manipulation with asynchronous off-policy updates. In _2017 IEEE International Confer-_
_ence on Robotics and Automation (ICRA)_, pp. 3389–3396. IEEE, 2017.


David Ha and J¨urgen Schmidhuber. Recurrent world models facilitate policy evolution. In _Advances_
_in Neural Information Processing Systems_, pp. 2455–2467, 2018.


Tuomas Haarnoja, Aurick Zhou, Pieter Abbeel, and Sergey Levine. Soft actor-critic: Offpolicy maximum entropy deep reinforcement learning with a stochastic actor. _arXiv_ _preprint_
_arXiv:1801.01290_, 2018a.


Tuomas Haarnoja, Aurick Zhou, Kristian Hartikainen, George Tucker, Sehoon Ha, Jie Tan, Vikash
Kumar, Henry Zhu, Abhishek Gupta, Pieter Abbeel, and Sergey Levine. Soft actor-critic algorithms and applications. _CoRR_, abs/1812.05905, 2018b. URL [http://arxiv.org/abs/](http://arxiv.org/abs/1812.05905)
[1812.05905.](http://arxiv.org/abs/1812.05905)


Karol Hausman, Jost Tobias Springenberg, Ziyu Wang, Nicolas Heess, and Martin Riedmiller.
Learning an embedding space for transferable robot skills. In _International Conference on Learn-_
_ing Representations_, 2018. [URL https://openreview.net/forum?id=rk07ZXZRb.](https://openreview.net/forum?id=rk07ZXZRb)


Nicolas Heess, Greg Wayne, Yuval Tassa, Timothy Lillicrap, Martin Riedmiller, and David Silver.
Learning and transfer of modulated locomotor controllers. _arXiv_ _preprint_ _arXiv:1610.05182_,
2016.


Nicolas Heess, Srinivasan Sriram, Jay Lemmon, Josh Merel, Greg Wayne, Yuval Tassa, Tom Erez,
Ziyu Wang, SM Eslami, Martin Riedmiller, et al. Emergence of locomotion behaviours in rich
environments. _arXiv preprint arXiv:1707.02286_, 2017.


Rein Houthooft, Xi Chen, Yan Duan, John Schulman, Filip De Turck, and Pieter Abbeel.
Curiosity-driven exploration in deep reinforcement learning via bayesian neural networks. _CoRR_,
abs/1605.09674, 2016. [URL http://arxiv.org/abs/1605.09674.](http://arxiv.org/abs/1605.09674)


12


Published as a conference paper at ICLR 2020


Robert A Jacobs, Michael I Jordan, Steven J Nowlan, Geoffrey E Hinton, et al. Adaptive mixtures
of local experts. _Neural computation_, 3(1):79–87, 1991.


Dmitry Kalashnikov, Alex Irpan, Peter Pastor, Julian Ibarz, Alexander Herzog, Eric Jang, Deirdre
Quillen, Ethan Holly, Mrinal Kalakrishnan, Vincent Vanhoucke, et al. Qt-opt: Scalable deep
reinforcement learning for vision-based robotic manipulation. _arXiv preprint arXiv:1806.10293_,
2018.


Sanket Kamthe and Marc Peter Deisenroth. Data-efficient reinforcement learning with probabilistic
model predictive control. _arXiv preprint arXiv:1706.06491_, 2017.


Diederik P Kingma and Jimmy Ba. Adam: A method for stochastic optimization. _arXiv_ _preprint_
_arXiv:1412.6980_, 2014.


Alexander S Klyubin, Daniel Polani, and Chrystopher L Nehaniv. Empowerment: A universal agentcentric measure of control. In _2005 IEEE Congress on Evolutionary Computation_, volume 1, pp.
128–135. IEEE, 2005.


Jonathan Ko, Daniel J Klein, Dieter Fox, and Dirk Haehnel. Gaussian processes and reinforcement learning for identification and control of an autonomous blimp. In _Proceedings 2007 ieee_
_international conference on robotics and automation_, pp. 742–747. IEEE, 2007.


Juˇs Kocijan, Roderick Murray-Smith, Carl Edward Rasmussen, and Agathe Girard. Gaussian process model based predictive control. In _Proceedings of the 2004 American Control Conference_,
volume 3, pp. 2214–2219. IEEE, 2004.


Vikash Kumar, Emanuel Todorov, and Sergey Levine. Optimal control with learned local models:
Application to dexterous manipulation. In _2016 IEEE International Conference on Robotics and_
_Automation (ICRA)_, pp. 378–383. IEEE, 2016.


Thanard Kurutach, Ignasi Clavera, Yan Duan, Aviv Tamar, and Pieter Abbeel. Model-ensemble
trust-region policy optimization. _arXiv preprint arXiv:1802.10592_, 2018.


Ian Lenz, Ross A Knepper, and Ashutosh Saxena. Deepmpc: Learning deep latent features for
model predictive control. In _Robotics:_ _Science and Systems_ . Rome, Italy, 2015.


Sergey Levine, Chelsea Finn, Trevor Darrell, and Pieter Abbeel. End-to-end training of deep visuomotor policies. _The Journal of Machine Learning Research_, 17(1):1334–1373, 2016.


Weiwei Li and Emanuel Todorov. Iterative linear quadratic regulator design for nonlinear biological
movement systems. In _ICINCO (1)_, pp. 222–229, 2004.


Volodymyr Mnih, Koray Kavukcuoglu, David Silver, Alex Graves, Ioannis Antonoglou, Daan Wierstra, and Martin Riedmiller. Playing atari with deep reinforcement learning. _arXiv_ _preprint_
_arXiv:1312.5602_, 2013.


Shakir Mohamed and Danilo Jimenez Rezende. Variational information maximisation for intrinsically motivated reinforcement learning. In _Advances_ _in_ _neural_ _information_ _processing_ _systems_,
pp. 2125–2133, 2015.


Ofir Nachum, Shixiang Shane Gu, Honglak Lee, and Sergey Levine. Data-efficient hierarchical
reinforcement learning. In _Advances in Neural Information Processing Systems_, pp. 3307–3317,
2018.


Anusha Nagabandi, Gregory Kahn, Ronald S Fearing, and Sergey Levine. Neural network dynamics
for model-based deep reinforcement learning with model-free fine-tuning. In _2018 IEEE Interna-_
_tional Conference on Robotics and Automation (ICRA)_, pp. 7559–7566. IEEE, 2018.


Junhyuk Oh, Xiaoxiao Guo, Honglak Lee, Richard L Lewis, and Satinder Singh. Action-conditional
video prediction using deep networks in atari games. In _Advances in neural information process-_
_ing systems_, pp. 2863–2871, 2015.


Pierre-Yves Oudeyer and Frederic Kaplan. What is intrinsic motivation? a typology of computational approaches. _Frontiers in neurorobotics_, 1:6, 2009.


13


Published as a conference paper at ICLR 2020


Pierre-Yves Oudeyer, Frdric Kaplan, and Verena V Hafner. Intrinsic motivation systems for autonomous mental development. _IEEE transactions on evolutionary computation_, 11(2):265–286,
2007.


Deepak Pathak, Pulkit Agrawal, Alexei A. Efros, and Trevor Darrell. Curiosity-driven exploration
by self-supervised prediction. In _ICML_, 2017.


Xue Bin Peng, Glen Berseth, KangKang Yin, and Michiel Van De Panne. Deeploco: Dynamic
locomotion skills using hierarchical deep reinforcement learning. _ACM Transactions on Graphics_
_(TOG)_, 36(4):41, 2017.


Theodore J Perkins, Doina Precup, et al. Using options for knowledge transfer in reinforcement
learning. _University of Massachusetts, Amherst, MA, USA, Tech. Rep_, 1999.


Aravind Rajeswaran, Vikash Kumar, Abhishek Gupta, Giulia Vezzani, John Schulman, Emanuel
Todorov, and Sergey Levine. Learning complex dexterous manipulation with deep reinforcement
learning and demonstrations. _arXiv preprint arXiv:1709.10087_, 2017.


Carl Edward Rasmussen. Gaussian processes in machine learning. In _Summer School on Machine_
_Learning_, pp. 63–71. Springer, 2003.


J¨urgen Schmidhuber. Formal theory of creativity, fun, and intrinsic motivation (1990–2010). _IEEE_
_Transactions on Autonomous Mental Development_, 2(3):230–247, 2010.


John Schulman, Sergey Levine, Pieter Abbeel, Michael I Jordan, and Philipp Moritz. Trust region
policy optimization. In _Icml_, volume 37, pp. 1889–1897, 2015.


John Schulman, Filip Wolski, Prafulla Dhariwal, Alec Radford, and Oleg Klimov. Proximal policy
optimization algorithms. _arXiv preprint arXiv:1707.06347_, 2017.


Sergio Guadarrama, Anoop Korattikara, Oscar Ramirez, Pablo Castro, Ethan Holly, Sam Fishman,
Ke Wang, Ekaterina Gonina, Chris Harris, Vincent Vanhoucke, Eugene Brevdo. TF-Agents:
A library for reinforcement learning in tensorflow. [https://github.com/tensorflow/](https://github.com/tensorflow/agents)
[agents,](https://github.com/tensorflow/agents) 2018. [URL https://github.com/tensorflow/agents.](https://github.com/tensorflow/agents) [Online; accessed
30-November-2018].


David Silver, Aja Huang, Chris J Maddison, Arthur Guez, Laurent Sifre, George Van Den Driessche,
Julian Schrittwieser, Ioannis Antonoglou, Veda Panneershelvam, Marc Lanctot, et al. Mastering
the game of go with deep neural networks and tree search. _nature_, 529(7587):484, 2016.


Noam Slonim, Gurinder S Atwal, Gasper Tkacik, and William Bialek. Estimating mutual information and multi–information in large networks. _arXiv preprint cs/0502017_, 2005.


Bradly C. Stadie, Sergey Levine, and Pieter Abbeel. Incentivizing exploration in reinforcement
learning with deep predictive models. _CoRR_, abs/1507.00814, 2015. URL [http://arxiv.](http://arxiv.org/abs/1507.00814)
[org/abs/1507.00814.](http://arxiv.org/abs/1507.00814)


Martin Stolle and Doina Precup. Learning options in reinforcement learning. In _International_
_Symposium on abstraction, reformulation, and approximation_, pp. 212–223. Springer, 2002.


Richard S Sutton, Doina Precup, and Satinder Singh. Between mdps and semi-mdps: A framework for temporal abstraction in reinforcement learning. _Artificial_ _intelligence_, 112(1-2):181–
211, 1999.


Haoran Tang, Rein Houthooft, Davis Foote, Adam Stooke, OpenAI Xi Chen, Yan Duan, John Schulman, Filip DeTurck, and Pieter Abbeel. # exploration: A study of count-based exploration for
deep reinforcement learning. In _Advances_ _in_ _neural_ _information_ _processing_ _systems_, pp. 2753–
2762, 2017.


Valentin Thomas, Emmanuel Bengio, William Fedus, Jules Pondard, Philippe Beaudoin, Hugo
Larochelle, Joelle Pineau, Doina Precup, and Yoshua Bengio. Disentangling the independently
controllable factors of variation by interacting with the world, 2018.


14


Published as a conference paper at ICLR 2020


Emanuel Todorov, Tom Erez, and Yuval Tassa. Mujoco: A physics engine for model-based control.
In _2012 IEEE/RSJ International Conference on Intelligent Robots and Systems_, pp. 5026–5033.
IEEE, 2012.


Alexander Sasha Vezhnevets, Simon Osindero, Tom Schaul, Nicolas Heess, Max Jaderberg, David
Silver, and Koray Kavukcuoglu. Feudal networks for hierarchical reinforcement learning. In
_Proceedings_ _of_ _the_ _34th_ _International_ _Conference_ _on_ _Machine_ _Learning-Volume_ _70_, pp. 3540–
3549. JMLR. org, 2017.


David Warde-Farley, Tom Van de Wiele, Tejas Kulkarni, Catalin Ionescu, Steven Hansen, and
Volodymyr Mnih. Unsupervised control through non-parametric discriminative rewards. _arXiv_
_preprint arXiv:1811.11359_, 2018.


Manuel Watter, Jost Springenberg, Joschka Boedecker, and Martin Riedmiller. Embed to control:
A locally linear latent dynamics model for control from raw images. In _Advances_ _in_ _neural_
_information processing systems_, pp. 2746–2754, 2015.


Grady Williams, Paul Drews, Brian Goldfain, James M Rehg, and Evangelos A Theodorou. Aggressive driving with model predictive path integral control. In _2016 IEEE International Conference_
_on Robotics and Automation (ICRA)_, pp. 1433–1440. IEEE, 2016.


A IMPLEMENTATION DETAILS


All of our models are written in the open source Tensorflow-Agents (Sergio Guadarrama, Anoop
Korattikara, Oscar Ramirez, Pablo Castro, Ethan Holly, Sam Fishman, Ke Wang, Ekaterina Gonina,
Chris Harris, Vincent Vanhoucke, Eugene Brevdo, 2018), based on Tensorflow (Abadi et al., 2015).


A.1 SKILL SPACES


When using discrete spaces, we parameterize _Z_ as one-hot vectors. These one-hot vectors are randomly sampled from the uniform prior _p_ ( _z_ ) = _D_ [1] [, where] _[ D]_ [ is the number of skills.] [We experiment]

with _D_ _≤_ 128. For discrete skills learnt for MuJoCo Ant in Section 6.3, we use _D_ = 20. For
continuous spaces, we sample _z_ _∼_ Uniform( _−_ 1 _,_ 1) _[D]_ . We experiment with _D_ = 2 for Ant learnt
with x-y prior, _D_ = 3 for Ant learnt without x-y prior (that is full observation space), to _D_ = 5 for
Humanoid on full observation spaces. The skills are sampled once in the beginning of the episode
and fixed for the rest of the episode. However, it is possible to resample the skill from the prior
within the episode, which allows for every skill to experience a different distribution than the initialization distribution. This also encourages discovery of skills which can be composed temporally.
However, this increases the hardness of problem, especially if the skills are re-sampled from the
prior frequently.


A.2 AGENT


We use SAC as the optimizer for our agent _π_ ( _a_ _|_ _s, z_ ), in particular, EC-SAC (Haarnoja et al.,
2018b). The _s_ input to the policy generally excludes global co-ordinates ( _x, y_ ) of the centre-ofmass, available for a lot of enviroments in OpenAI gym, which helps produce skills agnostic to the
location of the agent. We restrict to two hidden layers for our policy and critic networks. However,
to improve the expressivity of skills, it is beneficial to increase the capacity of the networks. The
hidden layer sizes can vary from (128 _,_ 128) for Half-Cheetah to (512 _,_ 512) for Ant and (1024 _,_ 1024)
for Humanoid. The critic _Q_ ( _s, a, z_ ) is similarly parameterized. The target function for critic _Q_ is
updated every iteration using a soft updates with co-efficient of 0 _._ 005. We use Adam (Kingma &
Ba, 2014) optimizer with a fixed learning rate of 3 _e −_ 4, and a fixed initial entropy co-efficient
_β_ = 0 _._ 1. While the policy is parameterized as a normal distribution _N_ ( _µ_ ( _s, z_ ) _,_ Σ( _s, z_ )) where Σ is
a diagonal covariance matrix, it undergoes through tanh transformation, to transform the output to
the range ( _−_ 1 _,_ 1) and constrain to the action bounds.


15


Published as a conference paper at ICLR 2020


A.3 SKILL-DYNAMICS


Skill-dynamics, denoted by _q_ ( _s_ _[′]_ _| s, z_ ), is parameterized by a deep neural network. A common trick
in model-based RL is to predict the ∆ _s_ = _s_ _[′]_ _−_ _s_, rather than the full state _s_ _[′]_ . Hence, the prediction
network is _q_ (∆ _s_ _|_ _s, z_ ). Note, both parameterizations can represent the same set of functions.
However, the latter will be easy to learn as ∆ _s_ will be centred around 0. We exclude the global coordinates from from the state input to _q_ . However, we can (and we still do) predict ∆ _x,_ ∆ _y_, because
reward functions for goal-based navigation generally rely on the position prediction from the model.
This represents another benefit of predicting state-deltas, as we can still predict changes in position
without explicitly knowing the global position.


The output distribution is modelled as a Mixture-of-Experts (Jacobs et al., 1991). We fix the number
of experts to be 4. We model each expert as a Gaussian distribution. The input ( _s, z_ ) goes through
two hidden layers (the same capacity as that of policy and critic networks, for example (512 _,_ 512)
for Ant). The output of the two hidden layers is used as an input to the mixture-of-experts, which
is linearly transformed to output the parameters of the Gaussian distribution, and a discrete distribution over the experts using a softmax distribution. In practice, we fix the covariance matrix of the
Gaussian experts to be an identity matrix, so we only need to output the means for the experts. We
use batch-normalization for both input and the hidden layers. We normalize the output targets using
their batch-average and batch-standard deviation, similar to batch-normalization.


A.4 OTHER HYPERPARAMETERS


The episode horizon is generally kept shorter for stable agents like Ant (200), while longer for
unstable agents like Humanoid (1000). For Ant, longer episodes do not add value, but Humanoid
can benefit from longer episodes as it helps it filter skills which are unstable. The optimization
scheme is on-policy, and we collect 2000 steps for Ant and 4000 steps for Humanoid in one iteration.
The intuition is to experience trajectories generated by multiple skills (approximately 10) in a batch.
Re-sampling skills can enable experiencing larger number of skills. Once a batch of episodes is
collected, the skill-dynamics is updated using Adam optimizer with a fixed learning rate of 3 _e −_ 4.
The batch size is 128, and we carry out 32 steps of gradient descent. To compute the intrinsic
reward, we need to resample the prior for computing the denominator. For continuous spaces, we
set _L_ = 500. For discrete spaces, we can marginalize over all skills. After the intrinsic reward is
computed, the policy and critic networks are updated for 128 steps with a batch size of 128. The
intuition is to ensure that every sample in the batch is seen for policy and critic updates about 3 _−_ 4
times in expectation.


A.5 PLANNING AND EVALUATION SETUPS


For evaluation, we fix the episode horizon to 200 for all models in all evaluation setups. Depending
upon the size of the latent space and planning horizon, the number of samples from the planning
distribution _P_ is varied between 10 _−_ 200. For _HP_ = 1 _, HZ_ = 10 and a 2 _D_ latent space, we use
50 samples from the planning distribution _P_ . The co-efficient _γ_ for MPPI is fixed to 10. We use
a setting of _HP_ = 1 and _HZ_ = 10 for dense-reward navigation, in which case we set the number
of refine steps _R_ = 10. However, for sparse reward navigation it is important to have a longer
horizon planning, in which case we set _HP_ = 4 _, HZ_ = 25 with a higher number of samples from
the planning distribution (200 from _P_ ). Also, when using longer planning horizons, we found that
smoothing the sampled plans help. Thus, if the sampled plan is _z_ 1 _, z_ 2 _, z_ 3 _, z_ 4 _. . ._, we smooth the plan
to make _z_ 2 = _βz_ 1 + (1 _−_ _β_ ) _z_ 2 and so on, with _β_ = 0 _._ 9.


For hierarchical controllers being learnt on top of low-level unsupervised primitives, we use PPO
(Schulman et al., 2017) for discrete action skills, while we use SAC for continuous skills. We keep
the number of steps after which the meta-action is decided as 10 (that is _HZ_ = 10). The hidden
layer sizes of the meta-controller are (128 _,_ 128). We use a learning rate of 1 _e_ _−_ 4 for PPO and 3 _e_ _−_ 4
for SAC.


For our model-based RL baseline PETS, we use an ensemble size of 3, with a fixed planning horizon of 20. For the model, we use a neural network with two hidden layers of size 400. In our
experiments, we found that MPPI outperforms CEM, so we report the results using the MPPI as our
controller.


16


Published as a conference paper at ICLR 2020


B GRAPHICAL MODELS, INFORMATION BOTTLENECK AND UNSUPERVISED
SKILL LEARNING


We now present a novel perspective on unsupervised skill learning, motivated from the literature on
information bottleneck. This section takes inspiration from (Alemi & Fischer, 2018), which helps
us provide a rigorous justification for our objective proposed earlier. To obtain our unsupervised RL
objective, we setup a graphical model _P_ as shown in Figure 9, which represents the distribution of
trajectories generated by a given policy _π_ . The joint distribution is given by:



_p_ ( _s_ 1 _, a_ 1 _. . . aT −_ 1 _, sT, z_ ) = _p_ ( _z_ ) _p_ ( _s_ 1)



_T −_ 1

- _π_ ( _at|st, z_ ) _p_ ( _st_ +1 _|st, at_ ) _._ (8)


_t_ =1



![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-16-1.png)











![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-16-0.png)



_a_ 1 _a_ 2 ... _aT_









Figure 9: Graphical model for the world _P_ in which
the trajectories are generated while interacting with
the environment. Shaded nodes represent the distributions we optimize.



Figure 10: Graphical model for the world _N_ which is
the desired representation of the world.



We setup another graphical model _N_, which represents the desired model of the world. In particular,
we are interested in approximating _p_ ( _s_ _[′]_ _|s, z_ ), which represents the transition function for a particular
primitive. This abstraction helps us get away from knowing the exact actions, enabling model-based
planning in behavior space (as discussed in the main paper). The joint distribution for _N_ shown in
Figure 10 is given by:



_η_ ( _s_ 1 _, a_ 1 _, . . . sT, aT, z_ ) = _η_ ( _z_ ) _η_ ( _s_ 1)



_T −_ 1

- _η_ ( _at_ ) _η_ ( _st_ +1 _|st, z_ ) _._ (9)


_t_ =1



The goal of our approach is to optimize the distribution _π_ ( _a|s, z_ ) in the graphical model _P_ to minimize the distance between the two distributions, when transforming to the representation of the
graphical model _Z_ . In particular, we are interested in minimizing the KL divergence between _p_ and
_η_, that is _DKL_ ( _p||η_ ). Note, if _N_ had the same structure as _P_, the information lost in projection
would be 0 for any valid _P_ . Interestingly, we can exploit the following result from in Friedman et al.
(2001) to setup the objective for _π_, without explicitly knowing _η_ :


min _DKL_ ( _p||η_ ) = _IP_ _−IN_ _,_ (10)
_η_


where _IP_ and _IN_ represents the multi-information for distribution _P_ on the respective graphical
models. Note, min _η∈N DKL_ ( _p||η_ ), which is the reverse information projection (Csisz´ar & Matus,
2003). The multi-information (Slonim et al., 2005) for a graphical model _G_ with nodes _gi_ is defined
as:

_IG_ =              - _I_ ( _gi_ ; _Pa_ ( _gi_ )) _,_ (11)


_i_


where _Pa_ ( _gi_ ) denotes the nodes upon which _gi_ has direct conditional dependence in _G_ . Using this
definition, we can compute the multi-information terms:



_T_

- _I_ ( _st_ ; _{st−_ 1 _, z}_ ) _._ (12)


_t_ =2



_T_

- _I_ ( _st_ ; _{st−_ 1 _, at−_ 1 _}_ ) and _IN_ =


_t_ =2


17



_IP_ =



_T_

- _I_ ( _at_ ; _{st, z}_ ) +


_t_ =1


Published as a conference paper at ICLR 2020


Following the Optimal Frontier argument in (Alemi & Fischer, 2018), we introduce Lagrange multipliers _βt_ _≥_ 0 _, δt_ _≥_ 0 for the information terms in _IP_ to setup an objective _R_ ( _π_ ) to be maximized
with respect to _π_ :



_R_ ( _π_ ) =



_T −_ 1

- _I_ ( _st_ +1; _{st, z}_ ) _−_ _βtI_ ( _at_ ; _{st, z}_ ) _−_ _δtI_ ( _st_ +1; _{st, at}_ ) (13)


_t_ =1


(14)



As the underlying dynamics are fixed and unknown, we simplify the optimization by setting _δt_ =
0 which intuitively corresponds to us neglecting the unchangeable information of the underlying
dynamics. This gives us



_R_ ( _π_ ) =


_≥_



_T −_ 1

- _I_ ( _st_ +1; _{st, z}_ ) _−_ _βtI_ ( _at_ ; _{st, z}_ ) (15)


_t_ =1


_T −_ 1

- _I_ ( _st_ +1; _z_ _| st_ ) _−_ _βtI_ ( _at_ ; _{st, z}_ ) (16)


_t_ =1



Here, we have used the chain rule of mutual information: _I_ ( _st_ +1; _{st, z}_ ) = _I_ ( _st_ +1; _st_ ) +
_I_ ( _st_ +1; _z_ _|_ _st_ ) _≥I_ ( _st_ +1; _z_ _|_ _st_ ), resulting from the non-negativity of mutual information. This
yield us an information bottleneck style objective where we maximize the mutual information motivated in Section 3, while minimizing _I_ ( _at_ ; _{st, z}_ ). We can show that the minimization of the latter
mutual information corresponds to entropy regularization of _π_ ( _at_ _| st, z_ ), as follows:




                - _[|][ s][t][, z]_ [)]
_I_ ( _at_ ; _{st, z}_ ) = E _at∼π_ ( _at|st,z_ ) _,st,z∼p_ log _[π]_ [(] _[a]_ _π_ _[t]_ ( _at_ )

                - _[|][ s][t][, z]_ [)]
= E _at∼π_ ( _at|st,z_ ) _,st,z∼p_ log _[π]_ [(] _[a]_ _p_ _[t]_ ( _at_ )

                - _[|][ s][t][, z]_ [)]
_≤_ E _at∼π_ ( _at|st,z_ ) _,st,z∼p_ log _[π]_ [(] _[a]_ _p_ _[t]_ ( _at_ )




(17)


_−DKL_ ( _π_ ( _at_ ) _|| p_ ( _at_ )) (18)


(19)



for some arbitrary distribution log _p_ ( _at_ ) (for example uniform). Again, we have used the nonnegativity of _DKL_ to get the inequality. We use Equation 19 in Equation 16 to get:



_R_ ( _π_ ) _≥_



_T −_ 1

- - 
_I_ ( _st_ +1; _z_ _| st_ ) _−_ _βt_ E _at∼π_ ( _at|st,z_ ) _,st,z∼p_ log _π_ ( _at_ _| st, z_ ) (20)
_t_ =1



where we have ignored _p_ ( _at_ ) as it is a constant with respect to optimization for _π_ . This motivates
the use of entropy regularization. We can follow the arguments in Section 3 to obtain an approximate lower bound for _I_ ( _st_ +1; _z_ _|_ _st_ ). The above discussion shows how DADS can be motivated
from a graphical modelling perspective, while justifying the use of entropy regularization from an
information bottleneck perspective. This objective also explicates the temporally extended nature of
_z_, and how it corresponds to a sequence of actions producing a predictable sequence of transitions
in the environment.



![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-17-0.png)











Figure 11: Graphical model for the world _P_ representing the stationary state, action distribution.
Shaded nodes represent the distributions we optimize.



Figure 12: Graphical model for the world _N_ using
which we is the representation we are interested in.



18


Published as a conference paper at ICLR 2020


We can carry out the exercise for the reward function in Eysenbach et al. (2018) (DIAYN) to provide
a graphical model interpretation of the objective used in the paper. To conform with objective
in the paper, we assume to be sampling to be state-action pairs from skill-conditioned stationary
distributions in the world _P_, rather than trajectories. The objective to be maximized is given by:


_R_ ( _π_ ) = _−IP_ + _IQ_ (21)
= _−I_ ( _a_ ; _{s, z}_ ) + _I_ ( _z_ ; _s_ ) (22)



= E _π_ [log _[p]_ [(] _[z][|][s]_ [)]



] (23)
_π_ ( _a_ )




[(] _[z][|][s]_ [)] _[π]_ [(] _[a][|][s, z]_ [)]

_p_ ( _z_ ) _[−]_ [log] _π_ ( _a_ )



_≥_ E _π_ [log _qφ_ ( _z|s_ ) _−_ log _p_ ( _z_ ) _−_ log _π_ ( _a|s, z_ )] = _R_ ( _π, qφ_ ) (24)

where we have used the variational inequalities to replace _p_ ( _z|s_ ) with _qφ_ ( _z|s_ ) and _π_ ( _a_ ) with a
uniform prior over bounded actions _p_ ( _a_ ) (which is ignored as a constant).


C APPROXIMATING THE REWARD FUNCTION


We revisit Equation 4 and the resulting approximate reward function constructed in Equation 6. The
maximization objective for policy was:

_R_ ( _π_ _| qφ_ ) = E _z,s,s′_ [�] log _qφ_ ( _s_ _[′]_ _| s, z_ ) _−_ log _p_ ( _s_ _[′]_ _| s_ )� (25)


The computational problem arises from the intractability of _p_ ( _s_ _[′]_ _|_ _s_ ) = - _p_ ( _s_ _[′]_ _|_ _s, z_ ) _p_ ( _z_ _|_ _s_ ) _dz_,
where both _p_ ( _s_ _[′]_ _|_ _s, z_ ) and _p_ ( _z_ _|_ _s_ ) _∝_ _p_ ( _s_ _|_ _z_ ) _p_ ( _z_ ) are intractable. Unfortunately, any variational
approximation results in an improper lower bound for the objective. To see that:

_R_ ( _π_ _| qφ_ ) = E _z,s,s′_ [�] log _qφ_ ( _s_ _[′]_ _| s, z_ ) _−_ log _q_ ( _s_ _[′]_ _| s_ )� _−DKL_ ( _p_ ( _s_ _[′]_ _| s_ ) _|| q_ ( _s_ _[′]_ _| s_ )) (26)

_≤_ E _z,s,s′_ [�] log _qφ_ ( _s_ _[′]_ _| s, z_ ) _−_ log _q_ ( _s_ _[′]_ _| s_ )� (27)

where the inequality goes the wrong way for any variational approximation _q_ ( _s_ _[′]_ _|_ _s_ ). Our approximation can be seen as a special instantiation of _q_ ( _s_ _[′]_ _|_ _s_ ) = - _qφ_ ( _s_ _[′]_ _|_ _s, z_ ) _p_ ( _z_ ) _dz_ . This
approximation is simple to compute as generating samples from the prior _p_ ( _z_ ) is inexpensive and
effectively requires only a forward pass through _qφ_ . Reusing _qφ_ to approximate _p_ ( _s_ _[′]_ _|_ _s_ ) makes
intuitive sense because we want _qφ_ to reasonably approximate _p_ ( _s_ _[′]_ _| s, z_ ) (which is why we collect
large batches of data and take multiple steps of gradient descent for fitting _qφ_ ). While sampling from
the prior _p_ ( _z_ ) is crude, sampling _p_ ( _z_ _|_ _s_ ) can be computationally prohibitive. For a certain class
of problems, especially locomotion, sampling from _p_ ( _z_ ) is a reasonable approximation as well. We
want our primitives/skills to be usable from any state, which is especially the case with locomotion.
Empirically, we have found our current approximation provides satisfactory results. We also discuss
some other potential solutions (and their limitations):


(a) One could potentially use another network _qβ_ ( _z_ _|_ _s_ ) to approximate _p_ ( _z_ _|_ _s_ ) by minimizing
E _s,z∼p_ - _DKL_ ( _p_ ( _z_ _|_ _s_ ) _||_ _qβ_ ( _z_ _|_ _s_ ))�. Note, the resulting approximation would still be an improper
lower bound for _R_ ( _π_ _|_ _qφ_ ). However, sampling from this _qβ_ might result in a better approximation
than sampling from the prior _p_ ( _z_ ) for some problems.


(b) We can bypass the computational intractability of _p_ ( _s_ _[′]_ _|_ _s_ ) by exploiting the variational lower
bounds from Agakov (2004). We use the following inequality, used in Hausman et al. (2018):


               _H_ ( _x_ ) _≥_ _p_ ( _x, z_ ) log _[q]_ [(] _[z][|][x]_ [)] (28)

_p_ ( _x, z_ ) _[dxdz]_


where _q_ is a variational approximation to the posterior _p_ ( _z|x_ ).

_I_ ( _s_ _[′]_ ; _z|s_ ) = _−H_ ( _s_ _[′]_ _|s, z_ ) + _H_ ( _s_ _[′]_ _|s_ ) (29)

_≥_ E _z,s,s′∼p_      - log _qφ_ ( _s_ _[′]_ _|s, z_ )] + E _z,s,s′∼p_      - log _qα_ ( _z|s_ _[′]_ _, s_ )� + _H_ ( _s_ _[′]_ _, z|s_ ) (30)

= E _z,s,s′∼p_        - log _qφ_ ( _s_ _[′]_ _|s, z_ ) + log _qα_ ( _z|s_ _[′]_ _, s_ )] + _H_ ( _s_ _[′]_ _, z|s_ ) (31)

where we have used the inequality for _H_ ( _s_ _[′]_ _|s_ ) to introduce the variational posterior for skill inference _qα_ ( _z_ _| s_ _[′]_ _, s_ ) besides the conventional variational lower bound to introduce _q_ ( _s_ _[′]_ _| s, z_ ). Further
decomposing the leftover entropy:

_H_ ( _s_ _[′]_ _, z|s_ ) = _H_ ( _z|s_ ) + _H_ ( _s_ _[′]_ _|s, z_ )


19


Published as a conference paper at ICLR 2020


Reusing the variational lower bound for marginal entropy from Agakov (2004), we get:


                 - [�]                 _H_ ( _s_ _[′]_ _|s, z_ ) _≥_ E _s,z_ _p_ ( _s_ _[′]_ _, a|s, z_ ) log _[q]_ [(] _[a][|][s][′][, s, z]_ [)] (32)

_p_ ( _s_ _[′]_ _, a|s, z_ ) _[ds][′][da]_

= _−_ log _c_ + _H_ ( _s_ _[′]_ _, a|s, z_ ) (33)

= _−_ log _c_ + _H_ ( _s_ _[′]_ _|s, a, z_ ) + _H_ ( _a|s, z_ ) (34)


Since, the choice of posterior is upon us, we can choose _q_ ( _a|s_ _[′]_ _, s, z_ ) = 1 _/c_ to induce a uniform
distribution for the bounded action space. For _H_ ( _s_ _[′]_ _|s, a, z_ ), notice that the underlying dynamics
_p_ ( _s_ _[′]_ _|s, a_ ) are independent of _z_, but the actions do depend upon _z_ . Therefore, this corresponds to
entropy-regularized RL when the dynamics of the system are deterministic. Even for stochastic
dynamics, the analogy might be a good approximation, assuming the underlying dynamics are not
very entropic. The final objective (making this low-entropy dynamics assumption) can be written
as:


_I_ ( _s_ _[′]_ ; _z|s_ ) _≥_ E _s_ E _p_ ( _s′,z|s_ )[log _qφ_ ( _s_ _[′]_ _|s, z_ ) + log _qα_ ( _z|s_ _[′]_ _, s_ ) _−_ log _p_ ( _z|s_ )] + _H_ ( _a|s, z_ ) (35)


While this does bypass the intractability of _p_ ( _s_ _[′]_ _|_ _s_ ), it runs into the intractable _p_ ( _z_ _|_ _s_ ), despite
deploying significant mathematical machinery and additional assumptions. Any variational approximation for _p_ ( _z_ _| s_ ) would again result in an improper lower bound for _I_ ( _s_ _[′]_ ; _z_ _| s_ ).


(c) One way to a make our approximation _q_ ( _s_ _[′]_ _|_ _s_ ) to more closely resemble _p_ ( _s_ _[′]_ _|_ _s_ ) is to change
our generative model _p_ ( _z, s, s_ _[′]_ ). In particular, if we resample _z_ _∼_ _p_ ( _z_ ) for every timestep of the
rollout from _π_, we can indeed write _p_ ( _z_ _|_ _s_ ) = _p_ ( _z_ ). Note, _p_ ( _s_ _[′]_ _|_ _s_ ) is still intractable to compute,
but marginalizing _qφ_ ( _s_ _[′]_ _|_ _s, z_ ) over _p_ ( _z_ ) becomes a better approximation of _p_ ( _s_ _[′]_ _|_ _s_ ). However,
this severely dampens the interpretation of our latent space _Z_ as temporally extended actions (or
skills). It becomes better to interpret the latent space _Z_ as dimensional reduction of action space.
Empirically, we found that this significantly throttles the learning, not yielding useful or interpretable
skills.


D INTERPOLATION IN CONTINUOUS LATENT SPACE


Figure 13: Interpolation in the continuous primitive space learned using DADS on the Ant environment corresponds to interpolation in the trajectory space. (Left) Interpolation from _z_ = [1 _._ 0 _,_ 1 _._ 0] (solid blue) to
_z_ = [ _−_ 1 _._ 0 _,_ 1 _._ 0] (dotted cyan); (Middle) Interpolation from _z_ = [1 _._ 0 _,_ 1 _._ 0] (solid blue) to _z_ = [ _−_ 1 _._ 0 _, −_ 1 _._ 0]
(dotted cyan); (Right) Interpolation from _z_ = [1 _._ 0 _,_ 1 _._ 0] (solid blue) to _z_ = [1 _._ 0 _, −_ 1 _._ 0] (dotted cyan).


E MODEL PREDICTION


From Figure 14, we observe that skill-dynamics can provide robust state-predictions over long planning horizons. When learning skill-dynamics with _x−y_ prior, we observe that the error in prediction
rises slower with horizon as compared to the norm of the actual position. This provides strong evidence of cooperation between the primitives and skill-dynamics learned using DADS with _x −_ _y_
prior. As the error-growth for skill-dynamics learned on full-observation space is sub-exponential,
similar argument can be made for DADS without _x −_ _y_ prior as well (albeit to a weaker extent).


20



![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-19-0.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-19-1.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-19-2.png)
Published as a conference paper at ICLR 2020


Figure 14: (Left) Prediction error in the Ant’s co-ordinates (normalized by the norm of the actual position)
for skill-dynamics. (Right) X-Y traces of actual trajectories (colored) compared to trajectories predicted by
skill-dynamics (dotted-black) for different skills.


21



![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-20-0.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-20-1.png)
