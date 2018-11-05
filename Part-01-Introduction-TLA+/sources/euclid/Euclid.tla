------------------------------- MODULE Euclid -------------------------------

EXTENDS Integers

CONSTANTS M, N
VARIABLES x, y

Init == (x = M) /\ (y = N)

Next == \/ /\ x < y
           /\ y' = y - x
           /\ x' = x
        \/ /\ y < x
           /\ x' = x-y
           /\ y' = y

Spec == Init /\ [][Next]_<<x,y>>

=============================================================================
\* Modification History
\* Last modified Fri Sep 14 09:38:44 GMT 2018 by luque
\* Created Fri Sep 14 09:38:33 GMT 2018 by luque
