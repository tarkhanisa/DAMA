type OperationResultProps = {
  title: string;
  result: unknown;
};

export function OperationResult({ title, result }: OperationResultProps) {
  if (!result) {
    return null;
  }

  return (
    <section className="operation-result">
      <h3>{title}</h3>
      <pre className="code-block">{JSON.stringify(result, null, 2)}</pre>
    </section>
  );
}
