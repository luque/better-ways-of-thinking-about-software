-------------------------------- MODULE Buffer ---------------------------------
(******************************************************************************)
(* This module simulates a producer-consumer example as it could be written   *)
(* using Java threads.  In particular, we want to demonstrate the risk of     *)
(* deadlock when producers and consumers wait on the same object.             *)
(******************************************************************************)
EXTENDS Naturals, Sequences

CONSTANTS Producers,   (* the (nonempty) set of producers                           *)
          Consumers,   (* the (nonempty) set of consumers                           *)
          BufCapacity, (* the maximum number of messages in the bounded buffer      *)
          Data         (* the set of values that can be produced and/or consumed    *)

ASSUME /\ Producers # {}                      (* at least one producer *)
       /\ Consumers # {}                      (* at least one consumer *)
       /\ Producers \intersect Consumers = {} (* no thread is both consumer and producer *)
       /\ BufCapacity > 0                     (* buffer capacity is at least 1 *)
       /\ Data # {}                           (* the type of data is nonenpty *) 
--------------------------------------------------------------------------------
VARIABLES buffer, (* the buffer, as a sequence of objects *)
          waitSet (* the wait set, as a set of threads *)

Participants == Producers \union Consumers
RunningThreads == Participants \ waitSet

TypeInv == /\ buffer \in Seq(Data)
           /\ Len(buffer) \in 0..BufCapacity
           /\ waitSet \subseteq Participants

Notify == IF waitSet # {}                                        (* corresponds to method notify() in Java *)
          THEN \E x \in waitSet : waitSet' = waitSet \ {x}
          ELSE UNCHANGED waitSet
    
NotifyAll == waitSet' = {}                                       (* corresponds to method notifyAll() in Java *)
    
Wait(t) == waitSet' = waitSet \union {t}                         (* corresponds to method wait() is Java *)
--------------------------------------------------------------------------------
Init == buffer = <<>> /\ waitSet = {}

Put(t,m) == IF Len(buffer) < BufCapacity
            THEN /\ buffer' = Append(buffer, m)
                 /\ Notify
            ELSE /\ Wait(t)
                 /\ UNCHANGED buffer

Get(t) == IF Len(buffer) > 0
          THEN /\ buffer' = Tail(buffer)
               /\ Notify
          ELSE /\ Wait(t)
               /\ UNCHANGED buffer

Next == \E t \in RunningThreads : \/ t \in Producers /\ \E m \in Data : Put(t,m)
                                  \/ t \in Consumers /\ Get(t)

Prog == Init /\ [][Next]_<<buffer, waitSet>>
--------------------------------------------------------------------------------
NoDeadlock == [](RunningThreads # {})

THEOREM Prog => []TypeInv /\ NoDeadlock

=============================================================================
\* Modification History
\* Last modified Fri Sep 14 10:21:37 GMT 2018 by luque
\* Created Fri Sep 14 10:21:27 GMT 2018 by luque
