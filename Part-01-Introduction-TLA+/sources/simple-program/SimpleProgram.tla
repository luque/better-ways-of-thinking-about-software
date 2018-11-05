--------------------------- MODULE SimpleProgram ---------------------------

EXTENDS Integers
VARIABLES i, pc

Init == (pc = "start") /\ (i = 0)

Pick == \/ /\ pc = "start"
           /\ i' \in 0..1000
           /\ pc' = "middle"

Add1 == \/ /\ pc = "middle"
           /\ i' = i + 1
           /\ pc' = "done"

Next == \/ Pick 
        \/ Add1


=============================================================================
\* Modification History
\* Last modified Fri Sep 14 09:27:32 GMT 2018 by luque
\* Created Fri Sep 14 09:26:19 GMT 2018 by luque
