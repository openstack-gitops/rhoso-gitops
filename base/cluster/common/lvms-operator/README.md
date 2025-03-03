# Deploy LVM Storage Operator

A storage domain is required for the control plane, and the simplest interface
is the LVM Storage Operator. Use of the `lvms-operator` directory can be used
to subscribe to the LVM Storage Operator and deploy a default storage domain
for the control plane.

## Using `lvms-operator`

The deployment of LVM Storage Operator and the `LVMCluster` manifest will
require environment specific configuration to be created. For more information
about the LVM Storage Operator, see [Persistent storage using Logical Volume
Manager
Storage](https://docs.openshift.com/container-platform/4.16/storage/persistent_storage/persistent_storage_local/persistent-storage-using-lvms.html)
in the OpenShift Storage guide.

### Identify disks by path

You can identify the disk paths available on a node by listing them in `/dev/disk/by-path` on the nodes:

_Procedure_

* Login to the node:
  ```
  $ oc debug node/<node_name>
  ```

* Run `chroot`:
  ```
  sh-5.1# chroot /host
  ```

* List the available disks by path:
  ```
  sh-5.1# ls /dev/disk/by-path
  pci-0000:00:1f.2-ata-6    pci-0000:01:00.0-scsi-0:0:0:0  pci-0000:01:00.0-scsi-0:0:1:0-part1  pci-0000:01:00.0-scsi-0:0:1:0-part3
  pci-0000:00:1f.2-ata-6.0  pci-0000:01:00.0-scsi-0:0:1:0  pci-0000:01:00.0-scsi-0:0:1:0-part2  pci-0000:01:00.0-scsi-0:0:1:0-part4
  ```

### Create kustomization

To extend the default manifests for LVM Storage Operator installation with GitOps, create the confirmation and patch for your environment.

_Prerequisites_

* identify the valid disk paths that LVM Storage Operator can use
* `kustomize` binary is available for local build testing

_Procedure_

* Create a directory for the `lvms-operator` configuration in your private git repo, such as `base/storage/`
  ```
  $ mkdir -p base/storage
  ```

* Create a patch file, such as `patch_lvmcluster_default.yaml` that contains the disks by path references:
  ```
  $ cat > base/storage/patch_lvmcluster_default.yaml <<EOF
  - op: replace
    path: /spec/storage/deviceClasses/0
    value:
      default: true
      deviceSelector:
        forceWipeDevicesAndDestroyAllData: true
        paths:
          - /dev/disk/by-path/pci-0000:01:00.0-scsi-0:0:0:0
      fstype: xfs
      name: vg1
      thinPoolConfig:
        name: thin-pool-1
        overprovisionRatio: 10
        sizePercent: 90
  EOF
  ```

* Create the `kustomization.yaml` to load the base manifests and patch the `LVMCluster` object:
  ```
  $ cat > base/storage/kustomization.yaml <<EOF
  apiVersion: kustomize.config.k8s.io/v1beta1
  kind: Kustomization

  resources:
    - https://github.com/openstack-gitops/rhoso-gitops/base/cluster/common/lvms-operator

  patches:
    - target:
        group: lvm.topolvm.io
        kind: LVMCluster
        version: v1alpha1
        name: lvmcluster-default
      path: patch_lvmcluster_default.yaml

  components:
    - https://github.com/openstack-gitops/rhoso-gitops/base/initialize/gitops/components/annotations
  EOF
  ```

* Validate the manifests with `kustomize build`:
  ```
  $ kustomize build base/storage
  ```

## Deploying LVM Storage Operator

You can deploy LVM Storage Operator with GitOps or directly with `oc apply -k`. To deploy with GitOps, create an `Application` manifest to load into GitOps referencing your private repo and path with the contents override.

_Prerequisites_

* Deployment of Red Hat GitOps. For more information, see the [GitOps bootstrap deployment playbook](../gitops).

_Procedure_

* Create an Application to load the LVM Storage Operator with GitOps, such as `application-lvms-operator.yaml`:

  **NOTE:** Replace `<private_git_server_path>` with the path of your private Git repository, for example, https://gitlab.private/rhoso-gitops/environments
  ```
  $ cat > application-lvms-operator.yaml <<EOF
  apiVersion: argoproj.io/v1alpha1
  kind: Application
  metadata:
    annotations:
      argocd.argoproj.io/sync-wave: "-10"
    name: deploy-lvms-operator
    namespace: openshift-gitops
    finalizers:
    - resources-finalizer.argocd.argoproj.io
  spec:
    destination:
      server: https://kubernetes.default.svc
    project: default
    source:
      path: base/storage
      repoURL: https://<private_git_server_repo_path>
      targetRevision: HEAD
    syncPolicy:
      automated: {}
  EOF
  ```
