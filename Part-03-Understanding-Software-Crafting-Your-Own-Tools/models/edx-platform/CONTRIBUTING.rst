########################
Contributing to the Open edX Platform
########################

Contributions to the Open edX Platform are very welcome, and strongly encouraged! We've
put together `some documentation that describes our contribution process`_,
but here's a step-by-step guide that should help you get started.

.. _some documentation that describes our contribution process: https://edx.readthedocs.org/projects/edx-developer-guide/en/latest/process/index.html

Step 0: Join the Conversation
=============================

Got an idea for how to improve the codebase? Fantastic, we'd love to hear about
it! Before you dive in and spend a lot of time and effort making a pull request,
it's a good idea to discuss your idea with other interested developers and/or the
edX product team. You may get some valuable feedback that changes how you think
about your idea, or you may find other developers who have the same idea and want
to work together.

Documentation
-------------

The Open edX documentation is at `https://docs.edx.org
<https://docs.edx.org>`_.  A number of topics are covered there, from
operations to development.

JIRA
----

If you've got an idea for a new feature or new functionality for an existing feature,
please start a discussion in the `development <https://discuss.openedx.org/c/development>`__
category of the discussion forum list to get feedback from the community about the idea
and your implementation choices.

If you then plan to contribute your code upstream, please `start a discussion on JIRA`_
(you may first need to `create a free JIRA account`_).
Start a discussion by visiting the JIRA website and clicking the "Create" button at the
top of the page. Choose the project "Open Source Pull Requests" and the issue type
"Feature Proposal". In the description give us as much detail as you can for the feature
or functionality you are thinking about implementing. Include a link to any relevant
forum discussions about your idea. We encourage you to do this before you begin
implementing your feature, in order to get valuable feedback from the edX product team
early on in your journey and increase the likelihood of a successful pull request.

.. _start a discussion on JIRA: https://openedx.atlassian.net/secure/Dashboard.jspa
.. _create a free JIRA account: https://openedx.atlassian.net/admin/users/sign-up

.. _forum:

Discussion forum
----------------

To ask technical questions and chat with the community, do not hesitate to join the
`Open edX discussion forum <https://discuss.openedx.org/>`__. There are different
categories for different topics:

- `Devops <https://discuss.openedx.org/c/devops>`__ for installation help
- `Development <https://discuss.openedx.org/c/development>`__, where Open edX developers
  unite
- `Community <https://discuss.openedx.org/c/community>`__ to discuss organizational
  matters in the open source community
- `Announcements <https://discuss.openedx.org/c/announcements>`__ where official Open edX
  announcement are made
- `Educators <https://discuss.openedx.org/c/educators>`__, to discuss online learning in general

Slack
-----

To talk with others in the Open edX community, join us on `Slack`_.
`Sign up for a free account`_ and join the conversation!
The group tends to be most active Monday through Friday
between 13:00 and 21:00 UTC (9am to 5pm US Eastern time),
but interesting conversations can happen at any time.
There are many different channels available for different topics, including:

* ``#events`` for upcoming events related to Open edX project
* ``#content`` for discussions about course content and creating the best courses

And lots more! You can also make your own channels to discuss new topics.

Note that Slack is no longer the recommended communication channel to ask about
technical issues. To do so, you should instead join the `official forum <#forum>`__.

.. _Slack: https://slack.com/
.. _Sign up for a free account: https://openedx-slack-invite.herokuapp.com/

Byte-sized Tasks & Bugs
-----------------------

If you are contributing for the first time and want a gentle introduction,
or if you aren't sure what to work on, have a look at the list of
`byte-sized bugs and tasks`_ in the tracker. These tasks are selected for their
small size, and usually don't require a broad knowledge of the edX platform.
It makes them good candidates for a first task, allowing you to focus on getting
familiar with the development environment and the contribution process.

.. _byte-sized bugs and tasks: http://bit.ly/edxbugs

Once you have identified a bug or task, `create an account on the tracker`_ and
then comment on the ticket to indicate that you are working on it. Don't hesitate
to ask clarifying questions on the ticket as needed, too, if anything is unclear.

.. _create an account on the tracker: https://openedx.atlassian.net/admin/users/sign-up

Step 1: Sign a Contribution Agreement
=====================================

Before edX can accept any code contributions from you, you'll need to sign the
`Individual Contributor Agreement`_. This confirms that you have the authority
to contribute the code in the pull request and ensures that edX can re-license
it.

.. _Individual Contributor Agreement: https://openedx.org/cla

If you will be contributing code on behalf of your employer or another
institution you are affiliated with, please reach out by email to openedx@edx.org
to request the Entity Contributor Agreement.

Once we have received and processed your agreement, we will reach out to you by
email to confirm. After that we can begin reviewing and merging your work.

Step 2: Fork, Commit, and Pull Request
======================================

GitHub has some great documentation on `how to fork a git repository`_. Once
you've done that, make your changes and `send us a pull request`_! Be sure to
include a detailed description for your pull request, so that a community
manager can understand *what* change you're making, *why* you're making it, *how*
it should work now, and how you can *test* that it's working correctly.

.. _how to fork a git repository: https://help.github.com/articles/fork-a-repo
.. _send us a pull request: https://help.github.com/articles/creating-a-pull-request

Step 3: Meet PR Requirements
============================

Our `contributor documentation`_ includes a long list of requirements that pull
requests must meet in order to be reviewed by a core committer. These requirements
include things like documentation and passing tests: see the
`contributor documentation`_ page for the full list.

.. _contributor documentation: https://edx.readthedocs.org/projects/edx-developer-guide/en/latest/process/contributor.html


Areas of particular concern with their own detailed guidelines are:

* `Accessibility`_: making sure our applications can
  be used by people with disabilities, in keeping with the edX
  `website accessibility policy`_.
* `Internationalization`_: enabling translation for use
  around the world.


.. _Accessibility: https://edx.readthedocs.org/projects/edx-developer-guide/en/latest/conventions/accessibility.html
.. _website accessibility policy: https://www.edx.org/accessibility
.. _Internationalization: https://edx.readthedocs.io/projects/edx-developer-guide/en/latest/internationalization/index.html

Step 4: Approval by Community Manager and Product Owner
=======================================================

A community manager will read the description of your pull request. If the
description is understandable, the community manager will send the pull request
to a product owner. The product owner will evaluate if the pull request is a
good idea for the Open edX platform, and if not, your pull request will be rejected. This
is another good reason why you should discuss your ideas with other members
of the community before working on a pull request!

Step 5: Code Review by Core Committer(s)
========================================

If your pull request meets the requirements listed in the
`contributor documentation`_, and it hasn't been rejected by a product owner,
then it will be scheduled for code review by one or more core committers. This
process sometimes takes awhile: most of the core committers on the project
are employees of edX, and they have to balance their time between code review
and new development.

Once the code review process has started, please be responsive to comments on
the pull request, so we can keep the review process moving forward.
If you are unable to respond for a few days, that's fine, but
please add a comment informing us of that -- otherwise, it looks like you're
abandoning your work!

Step 6: Merge!
==============

Once the core committers are satisfied that your pull request is ready to go,
one of them will merge it for you. Your code will end up on the edX production
servers in the next release, which usually which happens every week. Congrats!


############################
Expectations We Have of You
############################

By opening up a pull request, we expect the following things:

1. You've read and understand the instructions in this contributing file and
   the contribution process documentation.

2. You are ready to engage with the edX community. Engaging means you will be
   prompt in following up with review comments and critiques. Do not open up a
   pull request right before a vacation or heavy workload that will render you
   unable to participate in the review process.

3. If you have questions, you will ask them by either commenting on the pull
   request or asking us in the discussion forum or on Slack.

4. If you do not respond to comments on your pull request within 7 days, we
   will close it. You are welcome to re-open it when you are ready to engage.

############################
Expectations You Have of Us
############################

1. Within a week of opening up a pull request, one of our community managers
   will triage it, starting the documented contribution process. (Please
   give us a little extra time if you open the PR on a weekend or
   around a US holiday! We may take a little longer getting to it.)

2. We promise to engage in an active dialogue with you from the time we begin
   reviewing until either the PR is merged (by a core committer), or we
   decide that, for whatever reason, it should be closed.

3. Once we have determined through visual review that your code is not
   malicious, we will run a Jenkins build on your branch.
