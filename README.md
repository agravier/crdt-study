# LWW-element-graphs study

Using commutative interface operations simplifies the work of distributed 
systems designers [[ref](commutativity-sosp-13)]. Commutative replicated data 
types (CRDTs) make the most use of this advantage by allowing the design of 
distributed data structure that can continue operating during a temporary 
partition while still guaranteeing an eventual conflict-free merge.

This work examines LWW-element-graphs, a CRDT implementing undirected graphs.
After defining the terms by quoting the literature, we imagine a few use cases
in the form of applications centered around the collaborative distributed
editing of some type of document with a graph as its core structure. We then
discuss the design choices and constraints that lead to the LWW-element-graph
formulation. With those choices in mind, we consider some possible
implementations, their trade-offs and complexity, look at the problem of
timekeeping, discuss some optimizations, and formulate an implementation
checklist. We describe the attached software package, explain how to run, test
and extend it. Finally, we have a critical look at the realized implementation
and try to justify the choices and trade-offs.


## Key terminology 

from the [INRIA paper](inria-paper) (emphasis added):

> An **atom** is a base immutable data type, identified by its literal content.
Atoms can be copied between **processes**; atoms are equal if they have the same
content.

> An **object** is a mutable, replicated data type. Object types are
capitalised, e.g., “Set.” An object has an **identity**, a content (called its
*payload**), which may be any number of atoms or objects, an **initial state**,
and an **interface** consisting of **operations**. Two objects having the same
identity but located in different processes are called **replicas** of one
another.

> The environment consists of unspecified **clients** that query and modify
object state by calling operations in its interface, against a replica of their
choice called the **source replica**. A query executes locally, i.e., entirely
at one replica. An update has two phases: first, the client calls the operation
at the source, which may perform some initial processing. Then, the update is
transmitted asynchronously to all replicas; this is the **downstream** part.


## Example use cases of conflict-free replicated graph

The users of all imaginary applications described below must be able to 
work on the same document while isolated from each other. Eventually, once the
client applications communicate again, they are able to resolve the full set of 
changes and independently reach consensus about the merged document.  

### Collaborative diagramming application

_Graphviz Online_

Technical diagramming most often consists in creating components and connecting
them. This case is the closest match to the definition of an abstract graph,
although edges are often directed, and the graphical properties of elements
is os some importance. Nonetheless, a simplified prototype limited to immutable
strings connected by undirected edges would not be absurd.

In such an application, a document will typically contain dozens of vertices
and edges. A user will usually create or remove vertices and edges one at a
time.

### Collaborative vector drawing application

_Vectorized, MMO Krita_

This would correspond to an artistic illustration application where brush
strokes and graphic filters at application level result in the creation,
deletion and modification of many vertices and edges on the 2D plane. Note that
a modification can be modeled as a deletion followed by an addition, but as
graph components form meaningful objects and having vertices with mutable
location on the plane is important, it is likely that LWW-element-graphs alone
are insufficiently powerful to be suitable for this application. However, it is
useful to think about the performance characteristics of LWW-element-graphs in
this context as a thought exercise.

A single brush stroke can create and delete hundreds of points, and a document 
could easily contain hundreds of thousands of vertices and thousands of edges.

### Collaborative 3D modelling software

_Blender Bender_

3D authoring tools such as Blender or ZBrush operate on vertices located in 3D
space and connected by edges to form oriented polygons. Like for _Vectorized, 
MMO Krita_, many operations in _Blender Bender_ involve properties or location
transformations that render LWW-element-graphs less suitable.

Again, although LWW-element-graphs are likely to be the wrong tool for the job,
it is amusing to consider this application, as a document can contain millions
of edges and vertices.


### Collaborative Simultaneous Location And Mapping

_SLAM Swarm_

Imagine a group of autonomous mobile robots deployed in an unknown dynamic 
environment. Those robots need to individually study and map their surroundings
in order to move. Using LIDaR and computer vision techniques, they will be 
individually able to draw partial maps of their surroundings in the form of
graphs indicating physical obstruction, as observed from their location. Each
LIDaR vertex is timestamped, and edges are infered by computer vision 
techniques, with a numeric estimate of certainty.   

The robots will also be able to locate each other's relative frame of reference
by triangulation ([ref](triangulation-swarm)). Therefore, they have the
opportunity to create and collaboratively update a shared map of their
surroundings. LWW-element-graph is a suitable base data structure.

The number of edges and vertices will grow quickly even with process-level 
filtering and simplification, and the constraints of real-time processing on
embedded hardware make this a challenging and interesting use case to consider.


## Design discussion

### Approach

The central requirement of CRDTs is the mutual commutativity and associativity
of all operations that need to be eventually synchronized across clients. 

Due to the relative simplicity and functional nature of operation-based CRDTs, 
I took a CmRDT approach (as opposed to a state-based formulation). 
Computationally, they are equivalent, but they lead to different formulations.
Importantly, the op-based formulation is lighter on network resources.

The Last-Writer-Wins (LWW) family of approaches to independent, commutative
conflict resolution naturally lends itself to an operations-based object
specification. The requirement of LWW design is that "timestamps are assumed
unique, totally ordered, and consistent with causal order"
([INRIA](inria-paper)). This requires: 

- a monotonic clock within processes, and,
- an arbitrary level of tolerance for clock skew between processes, unless a 
  strong extrinsic clock synchronisation mechanism such as a vector
  clock or constant synchronisation with an NTP server is implemented (which
  would be inconsistent with the assumption that clients are only sporadically 
  connected).

In terms of network architecture, the easy way to guarantee finality with a
CmRDT is to centralize communication. Decentralized or hybrid architectures are
possible but less tolerant to Byzantine failure, and ensuring consistency
within a reasonable time and without the excessive use of broadcasting requires
work that falls out of the scope of this study.

The centralized architecture also helps alleviate the arbitrary clock skew
problem (see [Clocks](#clocks) section below), and, to some extent, reduces the
impact of a simple class of attacks around forged future timestamps.


### LWW element set design

The LWW-element-set is fully specified in the [reference paper](inria-paper),
therefore I will only shortly explain its principle here.

- A set contains atoms. I adapt the implementation by re-defining of an atom to
  be an **immutable ordered structure whose first element is an identifier**:
  _atom = ( identifier, payload )_. Two atoms are equal iff their identifiers 
  are equal.
- A process starts with an empty set (∅)
- A process may locally execute: 
  - a local set membership `lookup(atom)` predicate,
  - an `add(atom)` method, generating an _⟨ add(atom), ts ⟩_ operation
  - a `remove(atom)` method, generating a _⟨ remove(atom), ts ⟩_ operation


### LWW graph design

The LWW-element-graph

For collaborative applications where vertices are mainly characterized by their
identity (_Graphviz Online_), the constraints of the LWW-element-graph can not
be relaxed.

For collaborative creative applications where vertices are anonymous but
absolutely located in space, it is desirable that points in the canvas space
are not identified by their coordinates, but by an identifier that is at least
unique outside of the creating process. Depending on the modalities of the
creative application considered, an `add(vertex)` at the same location as an
existing one would still create a new vertex, f.e. if the existing vertex
relates to another brush or another stroke.

The reason is that in such applications, a vertex is first and foremost part of
a structure that is independent of other structures. A vertex' exact
coordinates may accidentally happen to overlap with the exact coordinates of a
vertex in another independent structure, and it would be allowed.

Hence, an `add_point` operation at application level should always use
`vertex_set.add` with a new atom containing a globally unique new identifier.
 

## Implementation

We define an abstract, language agnostic interface and discuss our
implementations of the processes and of the central server.


### Interfaces design

The central types of our study are presented in their mutable form.

Atoms must may be of any serializable type, but it must be possible to 
establish equality:

```
type Atom:
  equals(a: Atom) → Boolean
```

The implementation also requires a monotonic clock in each process:

```
type Clock:  -- Singleton within a process
  nanoseconds() → Integer  -- The current time in nanoseconds
  synchronize(ref: Integer)
```

The LWW-element-set functional interface as defined in the INRIA 
[paper](inria-paper):

```
type LWWSet<Atom>:
  clock: Clock
  add(a: Atom)
  remove(a: Atom)
  lookup(a: Atom) → Boolean
```

Edges are serializable, unordered pairs of atoms. Assuming that `Pair<A>` is a 
suitable type to represents an unordered pair, we have:

```
type Edge<Atom>:
  vertices: Pair<Atom>
  equals(e: Edge<Atom>) → Boolean
```

With Atoms representing vertices, we can now define the LWW-element-graph 
interface and the serialized LWW operations:

```
type LWWGraph<Atom>:
  clock: Clock
  vertices: LWWSet<Atom>
  edges: LWWSet<Edge<Atom>> 
  add_vertex(a: Atom)
  add_edge(e: Edge<Atom>)
  remove_vertex(a: Atom)
  remove_edge(e: Edge<Atom>)
  lookup_vertex(a: Atom) → Boolean
  lookup_edge(e: Edge<Atom>) → Boolean
```

```
type Operation<Atom> =  -- A union type 
  AddVertex(a: Atom, ts: int)    |
  AddEdge(e: Edge<Atom>, ts: int)      |
  RemoveVertex(a: Atom, ts: int) |
  RemoveEdge(e: Edge<Atom>, ts: int)
```

Finally, we need processes to form a tree. In our simplified application, we
are content with a single level (one server →  many clients):

```
type LWWGraphClient<Atom>:
  graph: LWWGraph<Atom>
  associate(s: Server)
  update(Collection<Operation<Atom>>)  -- Receive an update from the server

type LWWGraphServer:
  graph: LWWGraph<Atom>
  clients: Collection<Client>
  update(Collection<Operation<Atom>>)  -- Receive an update from a client
```


### Python immutable implementation of local process and backend server

The immutable implementation is simple, easily auditable, but highly
inefficient as it suffers from unbounded growth. Yet, it is useful as it
provides a reference implementation and a performance baseline.

### LSM-Tree based implementation of local process and backend server

Log-structured merge trees are datastructures that support a high write 
throughput and are naturally suited to LWW strategies.

### SQLite-based implementation of local process and backend server

The experimental SQLite 4 provides an implementation of LSM-Trees  
([ref](sqlite4-lsm)), and a Python [library](lsm-db) exists for it. 
Unfortunately, althought the Python library is maintained, the SQLite 4 
implementation of LSM Trees has not been ported to SQLite 3. So the risk of 
deprecation is high, and I didn't invest time in trying it out.

Instead, I created a simple SQLite table indexed on elements and timestamps,
which benefiting from fast insertion and retrieval. Regular compaction remains
necessary and moderately expensive, in the form of a query that resolves the 
latest state and writes it to a new file. 

```sqlite
CREATE INDEX key_ts_idx ON op_log(element, ts);
```

### Redis backend


### Elixir backend


### Clocks

LWW-based CRDTs assume shared knowledge of a global reference monotonic clock.
The monotonicity requirement is easily satisfied at the process level, but
correctly tracking a reference clock at the (distributed) system level over a
sporadic connection is not possible. We have accept some level of compromise.

To alleviate the problem, we devise a simple application clock synchronization 
protocol:

- The synchronization backend sends "timesync" messages containing the global
  application timestamp to each client. This global timestamp is sent to all
  clients both as a heartbeat and together with any other message. Each 
  timesync message is uniquely and sequentially indexed per process 
  (possibly modulo a large number).
- Processes track time with an internal monotonic clock. This clock is used to
  calculate the time elapsed since the last timesync message was received.
- Processes must keep track of the timestamp and index number of the last 
  timesync message received.
- When communicating with the server, processes must send two pieces of 
  information with each message:
  - The index number the last timesync message received
  - The process' best guess of the current global time 
- For each client process, the server must keep track of the indices and 
  timestamps of the timesyncs message since the last acknowledged one.
  
This primitive clock synchronization mechanism that may only address linear 
clock drift during disconnected periods, but it does alleviate the problem.
It can be trivially enhanced to make use of the estimated round-trip delay.


### Optimizations

#### Query filtering with Bloom Filters

Placing a Bloom Filter in front of the set membership query implementation can 
accelerate response. If the filter returns true, the actual set should still be 
queried, but it needs not if it returns false.

This is mostly of interest in slower or less scalable implementations like the 
LSM tree and SQLite implementations.

#### Locally concurrent and asynchronous operations

Procedures that implement the LWW-element-set interface functions must
generally be locally locking the data structure, because set membership would
otherwise be meaningless. 

However, this may not be necessary in an implementation tailored for those
collaborative creative applications where a new node is always created when a
new vertex is made. In this case, it would be possible to offer asynchronous
node creation tools that only block interacting tools. 

To take the example of the _MMO Krita_ application, that would mean that a
single brush stroke would be cached and concurrently processed by the local
LWW-element-graph while another, independent brush stroke could be applied to
the canvas by the user.

#### Checklist

[quiescent consistency] Does the design ensure conflict-free eventual 
consistency between all nodes without synchronization? 

[theoretical memory bounds] Does the design suffer from worst-case unbounded 
growth in degenerate cases where operations cancelling each other are applied 
a functionally constant-size object? (In other words, does garbage collection 
require synchronization?)


## Software package implementation

The overall principles and steps by which I worked the software that
accompanies this exploration were as follows:

- _Correctness first_. I will produce less features, but they will be correct.
  I rely on automated tests and static type checking.

- _Modular, reusable components_. I put an emphasis on the design of small
  interfaces that can be composed into providing the desired functionality.

- _Interface-first TDD_. I mostly create unit tests that are implementation 
  agnostic. They only rely on the public interface, and I apply them to each 
  implementation as I write it. 
  
- _Early BDD_. I create a toy CLI application that makes use of all features 
  of the library and define end-to-end behaviour tests this toy example.
  
- _Large-scale correctness tests with mocked time_. With a full implementation
  of one toy application, I create larger-scale application tests cases that
  verify the correctness of the end result in the presence of the real-world
  challenges to which the data structure is supposed to be resilient: network
  partitions, simultaneous operations by different processes on the same
  vertices/edges. These test would run on one host with the test controller 
  implementing the communication interface to mock network communication.

- _Large-scale real-time correctness and performance tests_. The same test 
  cases that are used with mocked time would be reused in a deployed 
  application in a private test network with local network communication 
  between processes and without the test controller interfering, but measuring
  real-time performance.
  

### Description of Python implementation

#### Code layout

Each module providing a functional interface with alternative implementation is
created as a 

#### Testing, packaging and dependencies

This is a library. Although I created an application to test it, the tests are
not packaged with the library, so all the application-specific libraries are
marked as development-only. Hence, the packaged library is rather lightweight
in terms of dependencies. This is generally a pattern that I favor.

Unit tests are run with _pytest_. Coverage is measured with _pytest-cov_. BDD
test scenarios for sample apps are described in Gherkin and run with _behave_.


## Critical discussion

### Coupling of serialization engine

### Relatively low performance of Python implementation


## Appendix: How I made this project

Prerequisites: pyenv, poetry

```shell
poetry new crdt-study --name crdt
cd crdt-study
git init .
git add *
git commit -m "Create project structure"
pyenv install --list | less
pyenv install 3.9.4
pyenv local 3.9.4
git add .python-version
git commit -m "Add pyenv marker for python version"
poetry add --dev pylint black mypy pytest-cov pydantic typer rich
# ...
```




[comment]: <> (References)

[commutativity-sosp-13]: https://dl.acm.org/doi/10.1145/2517349.2522712 "The scalable commutativity rule: designing scalable software for multicore processors"
[inria-paper]: https://hal.inria.fr/inria-00555588/en/  "A comprehensive study of Convergent and Commutative Replicated Data Types"
[triangulation-swarm]: https://doi.org/10.1109/SSRR.2007.4381290 "Localization Using Triangulation in Swarms of Autonomous Rescue Robots"
[sqlite4-lsm]: https://sqlite.org/src4/doc/trunk/www/lsmusr.wiki "SQLite4 LSM Users Guide"
[lsm-db]: https://lsm-db.readthedocs.io/en/latest/ "Python bindings for SQLite4 LSM"