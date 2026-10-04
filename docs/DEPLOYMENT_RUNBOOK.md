# Local deployment runbook

These commands are supplied for validation on your machine; they have not been executed against Docker or Kubernetes in the build workspace.

## Minikube demonstration

Start a Minikube cluster with a working container runtime. Run from the repository root:

```powershell
minikube start
minikube image build -t cloudops-observatory:local .
kubectl apply -f k8s/deployment.yaml
kubectl rollout status deployment/observatory
kubectl port-forward service/observatory 8080:8080
```

Open http://127.0.0.1:8080. Keep the port-forward terminal running. The PVC requires a default StorageClass with available storage. The demo runs one replica and Recreate deployment; there will be downtime on replacement.

## Diagnosis

```powershell
kubectl get pods,pvc
kubectl describe deployment observatory
kubectl logs deployment/observatory --tail=100
kubectl get events --sort-by=.metadata.creationTimestamp
```

ImagePullBackOff usually means the local image wasn't built in this cluster or the image name doesn't match. A Pending PVC needs a functioning storage provisioner. Permission errors on /data require checking the volume and UID/GID 10001 settings. Probe success only establishes HTTP server availability.

## Restart and recovery experiment

Capture the dashboard incident history, then:

```powershell
kubectl rollout restart deployment/observatory
kubectl rollout status deployment/observatory
```

Reconnect port-forward if interrupted. Verify incident history persisted. Restarting the pod doesn't repair the intentional failing endpoint.

## Container publication

Create a dedicated repository containing this folder's contents at its root. The manual Publish container on request workflow tests and builds before pushing a commit-tagged image to GHCR. It requires package write permissions; public repository visibility does not necessarily make the package public. Review package visibility separately. The automatic test workflow does not publish images.

## Cleanup

```powershell
kubectl delete deployment observatory
kubectl delete service observatory
```

Keep the PVC for history. Delete it only when you intend to discard the data:

```powershell
kubectl delete pvc observatory-data
```

## Reference documentation

- https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images
- https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/

AWS hosting is a later phase. No paid resources are created by these files.
