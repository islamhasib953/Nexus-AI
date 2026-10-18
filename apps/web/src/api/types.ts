export type HealthResponse = {
  status: string;
  service: string;
  version: string;
};

export type ContractSummary = {
  api_version: string;
  service: string;
  phase: number;
  status: string;
  streaming: string;
  model_provider: string;
  routes: string[];
};
