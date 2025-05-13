---
title: "Helm Object Ordering"
date: 2025-03-21T07:22:00-04:00
draft: false
categories: ["helm", "kubernetes"]
tags: ["helm", "kubernetes", "pitfalls"]
---

Sometimes I forget that Helm just manages templates on top of Kubernetes. There are also "pitfalls" I used to run into. 

When Helm installs or upgrades charts, the Kubernetes objects from the charts and/or dependencies are: 

- aggregated into a single set; then
- sorted by type followed by name; and then 
- created/updated in that order

The ordering of installed Kubernetes objects when using `helm install` or `helm upgrade` looks like this:

```plaintext
1) Namespace
2) NetworkPolicy
3) ResourceQuota
4) LimitRange
5) PodSecurityPolicy
6) PodDisruptionBudget
7) Secret
8) ConfigMap
9) StorageClass
10) PersistentVolume
11) PersistentVolumeClaim
12) ServiceAccount
13) CustomResourceDefinition
14) ClusterRole
15) ClusterRoleList
16) ClusterRoleBinding
17) ClusterRoleBindingList
18) Role
19) RoleList
20) RoleBinding
21) RoleBindingList
22) Service
23) DaemonSet
24) Pod
25) ReplicationController
26) ReplicaSet
27) Deployment
28) HorizontalPodAutoscaler
29) StatefulSet
30) Job
31) CronJob
32) Ingress
33) APIService
```
[ref - kind_sorter.go](https://github.com/helm/helm/blob/484d43913f97292648c867b56768775a55e4bba6/pkg/releaseutil/kind_sorter.go)

Lame. Helm leaves a lot to be desired, even with it being the de-facto standard of deploying applications and products on top of Kubernetes. 

So we cannot install objects in a "deterministic order." This extends into Helm dependencies clause, which can be packaged "alongside" your main application chart. 

But this normally fails with more complex setups, where your application needs certain actions to be completed before certain Helm charts are installed.
