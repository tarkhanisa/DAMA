type FormStatusProps = {
  type: "idle" | "success" | "error";
  message?: string;
};

export function FormStatus({ type, message }: FormStatusProps) {
  if (!message) {
    return null;
  }

  return <p className={`form-status form-status-${type}`}>{message}</p>;
}
