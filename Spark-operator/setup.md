# Install Spark-operator
```bash
# adding helm repo
helm repo add spark-operator https://kubeflow.github.io/spark-operator
helm repo update

cat <<EOF > values.yaml
spark:
    jobNamespaces:
    - {{namespaceToRunSparkOperator}} # here i would use zeatarou
EOF

helm install zeatarou spark-operator/spark-operator -f values.yaml -n spark-operator --debug
```