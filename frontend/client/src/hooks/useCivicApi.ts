import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as api from "@/lib/api";

export function useCivicHealth() {
  return useQuery({
    queryKey: ["civic", "health"],
    queryFn: () => api.getHealth(),
  });
}

export function useCivicMe() {
  return useQuery({
    queryKey: ["civic", "me"],
    queryFn: () => api.getMe(),
  });
}

export function useAnalyzeRights() {
  return useMutation({
    mutationFn: ({ problem, language = "en" }: { problem: string; language?: string }) =>
      api.analyzeRights(problem, language),
  });
}

export function useConversations() {
  return useQuery({
    queryKey: ["civic", "conversations"],
    queryFn: () => api.getConversations(),
  });
}

export function useConversation(conversationId: string | null) {
  return useQuery({
    queryKey: ["civic", "conversation", conversationId],
    queryFn: () => (conversationId ? api.getConversation(conversationId) : null),
    enabled: Boolean(conversationId),
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ service = "rights", language = "hinglish" }: { service?: string; language?: string }) =>
      api.createConversation(service, language),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["civic", "conversations"] });
    },
  });
}

export function useSendMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ conversationId, message }: { conversationId: string; message: string }) =>
      api.sendChatMessage(conversationId, message),
    onSuccess: (_, { conversationId }) => {
      queryClient.invalidateQueries({ queryKey: ["civic", "conversation", conversationId] });
    },
  });
}

export function useForms() {
  return useQuery({
    queryKey: ["civic", "forms"],
    queryFn: () => api.getForms(),
  });
}

export function useFormDefinition(formId: string | null) {
  return useQuery({
    queryKey: ["civic", "form", formId],
    queryFn: () => (formId ? api.getFormDefinition(formId) : null),
    enabled: Boolean(formId),
  });
}

export function useCreateFormSession() {
  return useMutation({
    mutationFn: (formId: string) => api.createFormSession(formId),
  });
}

export function useFormSession(sessionId: string | null) {
  return useQuery({
    queryKey: ["civic", "formSession", sessionId],
    queryFn: () => (sessionId ? api.getFormSession(sessionId) : null),
    enabled: Boolean(sessionId),
  });
}

export function useUpdateFormSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ sessionId, data }: { sessionId: string; data: Record<string, any> }) =>
      api.updateFormSession(sessionId, data),
    onSuccess: (_, { sessionId }) => {
      queryClient.invalidateQueries({ queryKey: ["civic", "formSession", sessionId] });
    },
  });
}

export function useGenerateComplaint() {
  return useMutation({
    mutationFn: (params: {
      form_session_id?: string;
      language?: string;
      name?: string;
      person?: string;
      issue?: string;
      extra?: string;
      title?: string;
    }) => api.generateComplaint(params),
  });
}

export function useComplaint(complaintId: string | null) {
  return useQuery({
    queryKey: ["civic", "complaint", complaintId],
    queryFn: () => (complaintId ? api.getComplaint(complaintId) : null),
    enabled: Boolean(complaintId),
  });
}

export function useSourceDetails(sourceId: string | null) {
  return useQuery({
    queryKey: ["civic", "source", sourceId],
    queryFn: () => (sourceId ? api.getSource(sourceId) : null),
    enabled: Boolean(sourceId),
  });
}

export function useRAGQuery() {
  return useMutation({
    mutationFn: (params: {
      query: string;
      top_k?: number;
      candidate_k?: number;
      document_type?: string;
    }) => api.queryRAG(params),
  });
}

export function useRTIDraft() {
  return useMutation({
    mutationFn: (params: {
      request: string;
      applicant_name?: string;
      applicant_address?: string;
      public_authority?: string;
    }) => api.draftRTI(params),
  });
}

