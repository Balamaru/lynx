# Setup Spark-operator
```bash
# adding helm repo
helm repo add spark-operator https://kubeflow.github.io/spark-operator
helm repo update

helm install zeatarou spark-operator/spark-operator -f values.yaml -n zeatarou --debug
```