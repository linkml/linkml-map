# linkml-transformer

See [these slides](https://docs.google.com/presentation/d/1ctgT1IfwPjnFQO2Q0sYlM8qk0wiB2_32JyeKyN4Uf8k/edit)

## Examples

### Measurements

```yaml
- id: P:001
  height:
    value: 172.0
    unit: cm
```

<==>

```yaml
- id: P:001
  height_in_cm: 172.0
```

<==>

```yaml
- id: P:001
  height: "172.0 cm"
```
