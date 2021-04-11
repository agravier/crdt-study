# LWW-element-Graphs study

## Key terminology 

from the [INRIA paper](inria-paper) (emphasis added):

> An **atom** is a base immutable data type, identified by its literal content.
Atoms can be copied between **processes**; atoms are equal if they have the same
content.

> An **object** is a mutable, replicated data type. Object types are
capitalised, e.g., “Set.” An object has an **identity**, a content (called its
**payload**), which may be any number of atoms or objects, an **initial state**,
and an **interface** consisting of **operations**. Two objects having the same identity
but located in different processes are called **replicas** of one another.

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

_Graphviz online_

Technical diagramming most often consists in creating components and connecting
them. This case is the closest match to the definition of an abstract graph,
although some direction and graphical properties are often important.
Nonetheless, a case limited to immutable strings connected by undirected edges
could be considered.

A document will typically contain dozens of vertices and edges. A user will 
usually create or remove vertices and edges one at a time. 

### Collaborative vector drawing application

_Vectorized, MMO Krita_

This would correspond to an artistic illustration application where brush
strokes and graphic filters at application level result in the creation,
deletion and modification of many vertices and edges on the 2D plane. Note that
a modification can be modeled as a deletion followed by an addition, but as
graph components form meaningful objects and mutable location on the plane is
important, it is likely that LWW-Graphs alone are insufficiently powerful to be
suitable for this application. But it is useful to think about the performance
characteristics of LWW-element-Graphs in this context as a thought exercise.

A single brush stroke can create and delete hundreds of points, and a document 
could easily contain hundreds of thousands of vertices and thousands of edges. 


### Collaborative 3D modelling software

_Blender bender_

3D authoring tools such as Blender or ZBrush operate on vertices located in 3D
space and connected by edges to form oriented polygons.

Although LWW-element-graphs are likely to be the wrong tool for the job, it is
amusing to consider this application, as a document can contain millions of 
edges and vertices.   


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

The LWW-element-Set is fully specified in the [reference paper](inria-paper),
therefore I will only shortly explain its principle here.

- A set contains atoms. I adapt the implementation by re-defining
  of an atom to be an **immutable ordered structure whose first element is an
  identifier**: _atom = ( identifier, payload )_. Two atoms are equal iff their 
  identifiers are equal.
- A process starts with an empty set (∅)
- A process may locally execute: 
  - a local set membership `lookup(atom)` predicate,
  - an `add(atom)` method, generating an _⟨ add(atom), ts ⟩_ operation
  - a `remove(atom)` method, generating a _⟨ remove(atom), ts ⟩_ operation
    



### LWW graph design

For 

For collaborative creative applications, it is desirable that points in the 
canvas space are not identified by their coordinates, but by an identifier that
is namespaced to the creating process. Hence, an add_point operation at 
application level should always use vertex_set.add with a new atom containing 
a globally unique new identifier. Therefore, 

`add_vertex(atom)`

 

## Implementation

We define an abstract, language agnostic interface and discuss alternative 
implementations of the processes and of the central server.

### Interface




lookup

add_vertex

add_edge

remove_vertex

remove_edge



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

LWW-based CRDTs assume shared knowledge of a global reference monotonous clock.
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
- Processes track time with an internal monotonous clock. This clock is used to
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

This is mostly of interest in slower or less scalable implementations like the 
LSM tree and SQLite implementations.

#### Asynchronous operations

#### Checklist

[quiescent consistency] Does the design ensure conflict-free eventual 
consistency between all nodes without synchronization? 

[theoretical memory bounds] Does the design suffer from worst-case unbounded 
growth in degenerate cases where operations cancelling each other are applied 
a functionally constant-size object? (In other words, does garbage collection 
require synchronization?)


## How I made this project

Prerequisites: pyenv, poetry

```shell
poetry new goodnotes-crdt-study --name crdt
cd goodnotes-crdt-study
git init .
git add *
git commit -m "Create project structure"
pyenv install --list | less
pyenv install 3.9.4
pyenv local 3.9.4
git add .python-version
git commit -m "Add pyenv marker for python version"
```




[comment]: <> (References)

[inria-paper]: https://hal.inria.fr/inria-00555588/en/  "A comprehensive study of Convergent and Commutative Replicated Data Types"
[sqlite4-lsm]: https://sqlite.org/src4/doc/trunk/www/lsmusr.wiki "SQLite4 LSM Users Guide"
[lsm-db]: https://lsm-db.readthedocs.io/en/latest/ "Python bindings for SQLite4 LSM"