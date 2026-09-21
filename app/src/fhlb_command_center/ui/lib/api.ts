import { useQuery, useSuspenseQuery, useMutation } from "@tanstack/react-query";
import type { UseQueryOptions, UseSuspenseQueryOptions, UseMutationOptions } from "@tanstack/react-query";
export class ApiError extends Error {
    status: number;
    statusText: string;
    body: unknown;
    constructor(status: number, statusText: string, body: unknown){
        super(`HTTP ${status}: ${statusText}`);
        this.name = "ApiError";
        this.status = status;
        this.statusText = statusText;
        this.body = body;
    }
}
export interface AlertAckIn {
    alert_key: string;
    note?: string | null;
    persona: string;
}
export interface AlertAckOut {
    acknowledged_by: string;
    alert_key: string;
    created_at: string;
    id: string;
    note?: string | null;
    persona: string;
}
export interface AnnotationIn {
    body: string;
    persona: string;
    widget_key: string;
}
export interface AnnotationOut {
    author: string;
    body: string;
    created_at: string;
    id: string;
    persona: string;
    widget_key: string;
}
export interface AnomalyResponse {
    blocks?: Record<string, unknown>[] | null;
    content?: string;
    engine?: string;
    exists?: boolean;
    generated_at?: string | null;
    generated_by?: string | null;
    high?: number;
    low?: number;
    medium?: number;
    persona: string;
    scan_date?: string | null;
    sources?: Record<string, unknown>[] | null;
    stale?: boolean;
    steps?: number | null;
    summary?: string | null;
}
export interface AssistantRequest {
    persona?: string;
    question: string;
}
export interface BriefingResponse {
    gateway?: GovernedResponse | null;
    generated_at?: string | null;
    genie_agent?: GovernedResponse | null;
    persona: string;
    stale?: boolean;
}
export interface ComplexValue {
    display?: string | null;
    primary?: boolean | null;
    ref?: string | null;
    type?: string | null;
    value?: string | null;
}
export interface EarlyWarningDriver {
    contribution: number;
    direction: string;
    feature: string;
    label: string;
    value?: number | null;
}
export interface EarlyWarningItem {
    advances_mm?: number | null;
    drivers?: EarlyWarningDriver[];
    internal_rating?: string | null;
    member_id: string;
    member_name: string;
    member_type?: string | null;
    pd_12m: number;
    rating_gap?: boolean;
    rating_num?: number | null;
    recommended_action: string;
    risk_band: string;
}
export interface EarlyWarningResponse {
    cached?: boolean;
    elevated?: number;
    endpoint: string;
    generated_at?: string | null;
    high?: number;
    items?: EarlyWarningItem[];
    model_version?: string | null;
    rating_gaps?: number;
    scored?: number;
}
export interface EarlyWarningScoreRequest {
    member_id: string;
}
export interface ExamPackItemIn {
    label: string;
    source_ref: string;
    source_type: string;
}
export interface ExamPackItemOut {
    created_at: string;
    id: string;
    label: string;
    source_ref: string;
    source_type: string;
}
export interface ExamRequestIn {
    due_date?: string | null;
    examiner: string;
    title: string;
}
export interface ExamRequestOut {
    created_at: string;
    created_by: string;
    due_date?: string | null;
    examiner: string;
    id: string;
    items?: ExamPackItemOut[];
    status: string;
    title: string;
}
export interface Freshness {
    as_of?: string | null;
}
export interface GenieAgentRequest {
    conversation_id?: string | null;
    question: string;
}
export interface GenieRequest {
    conversation_id?: string | null;
    question: string;
}
export interface GenieResponse {
    answer: string;
    columns?: string[];
    conversation_id?: string | null;
    message_id?: string | null;
    rows?: Record<string, unknown>[];
    sql?: string | null;
    viz?: GenieViz | null;
}
export interface GenieViz {
    attachment_id: string;
    message_id?: string | null;
    title?: string | null;
}
export interface GovernanceInfo {
    content_sources?: Record<string, unknown>[];
    endpoint: string;
    guardrails?: Record<string, unknown>;
    inference_table?: string | null;
    rate_limits?: Record<string, unknown>[];
    recent_audit?: Record<string, unknown>[];
    usage_tracking?: boolean;
}
export interface GovernedResponse {
    blocks?: Record<string, unknown>[] | null;
    content: string;
    endpoint: string;
    engine?: string;
    follow_ups?: string[];
    guardrail_verdict: string;
    latency_ms?: number | null;
    request_id?: string | null;
    sources?: Record<string, unknown>[] | null;
    steps?: number | null;
}
export interface HTTPValidationError {
    detail?: ValidationError[];
}
export interface Name {
    family_name?: string | null;
    given_name?: string | null;
}
export interface NarrativeRequest {
    engine?: string | null;
    persona?: string;
}
export interface Rows {
    columns?: string[];
    rows?: Record<string, unknown>[];
}
export interface User {
    active?: boolean | null;
    display_name?: string | null;
    emails?: ComplexValue[] | null;
    entitlements?: ComplexValue[] | null;
    external_id?: string | null;
    groups?: ComplexValue[] | null;
    id?: string | null;
    name?: Name | null;
    roles?: ComplexValue[] | null;
    schemas?: UserSchema[] | null;
    user_name?: string | null;
}
export const UserSchema = {
    "urn:ietf:params:scim:schemas:core:2.0:User": "urn:ietf:params:scim:schemas:core:2.0:User",
    "urn:ietf:params:scim:schemas:extension:workspace:2.0:User": "urn:ietf:params:scim:schemas:extension:workspace:2.0:User"
} as const;
export type UserSchema = typeof UserSchema[keyof typeof UserSchema];
export interface ValidationError {
    ctx?: Record<string, unknown>;
    input?: unknown;
    loc: (string | number)[];
    msg: string;
    type: string;
}
export interface VersionOut {
    version: string;
}
export interface WatchlistIn {
    member_id: string;
    member_name: string;
    reason: string;
    severity?: string;
}
export interface WatchlistItemOut {
    added_by: string;
    created_at: string;
    id: string;
    member_id: string;
    member_name: string;
    reason: string;
    severity: string;
}
export interface GetAnomaliesParams {
    persona: string;
}
export const getAnomalies = async (params: GetAnomaliesParams, options?: RequestInit): Promise<{
    data: AnomalyResponse;
}> =>{
    const res = await fetch(`/api/ai/anomalies/${params.persona}`, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const getAnomaliesKey = (params?: GetAnomaliesParams)=>{
    return [
        "/api/ai/anomalies/{persona}",
        params
    ] as const;
};
export function useGetAnomalies<TData = {
    data: AnomalyResponse;
}>(options: {
    params: GetAnomaliesParams;
    query?: Omit<UseQueryOptions<{
        data: AnomalyResponse;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: getAnomaliesKey(options.params),
        queryFn: ()=>getAnomalies(options.params),
        ...options?.query
    });
}
export function useGetAnomaliesSuspense<TData = {
    data: AnomalyResponse;
}>(options: {
    params: GetAnomaliesParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: AnomalyResponse;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: getAnomaliesKey(options.params),
        queryFn: ()=>getAnomalies(options.params),
        ...options?.query
    });
}
export interface RunAnomaliesParams {
    persona: string;
    "X-Forwarded-Host"?: string | null;
    "X-Forwarded-Preferred-Username"?: string | null;
    "X-Forwarded-User"?: string | null;
    "X-Forwarded-Email"?: string | null;
    "X-Request-Id"?: string | null;
    "X-Forwarded-Access-Token"?: string | null;
}
export const runAnomalies = async (params: RunAnomaliesParams, options?: RequestInit): Promise<{
    data: AnomalyResponse;
}> =>{
    const res = await fetch(`/api/ai/anomalies/${params.persona}`, {
        ...options,
        method: "POST",
        headers: {
            ...(params?.["X-Forwarded-Host"] != null && {
                "X-Forwarded-Host": params["X-Forwarded-Host"]
            }),
            ...(params?.["X-Forwarded-Preferred-Username"] != null && {
                "X-Forwarded-Preferred-Username": params["X-Forwarded-Preferred-Username"]
            }),
            ...(params?.["X-Forwarded-User"] != null && {
                "X-Forwarded-User": params["X-Forwarded-User"]
            }),
            ...(params?.["X-Forwarded-Email"] != null && {
                "X-Forwarded-Email": params["X-Forwarded-Email"]
            }),
            ...(params?.["X-Request-Id"] != null && {
                "X-Request-Id": params["X-Request-Id"]
            }),
            ...(params?.["X-Forwarded-Access-Token"] != null && {
                "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"]
            }),
            ...options?.headers
        }
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useRunAnomalies(options?: {
    mutation?: UseMutationOptions<{
        data: AnomalyResponse;
    }, ApiError, {
        params: RunAnomaliesParams;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>runAnomalies(vars.params),
        ...options?.mutation
    });
}
export const aiAssistant = async (data: AssistantRequest, options?: RequestInit): Promise<{
    data: GovernedResponse;
}> =>{
    const res = await fetch("/api/ai/assistant", {
        ...options,
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...options?.headers
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useAiAssistant(options?: {
    mutation?: UseMutationOptions<{
        data: GovernedResponse;
    }, ApiError, AssistantRequest>;
}) {
    return useMutation({
        mutationFn: (data)=>aiAssistant(data),
        ...options?.mutation
    });
}
export interface GetBriefingsParams {
    persona: string;
}
export const getBriefings = async (params: GetBriefingsParams, options?: RequestInit): Promise<{
    data: BriefingResponse;
}> =>{
    const res = await fetch(`/api/ai/briefings/${params.persona}`, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const getBriefingsKey = (params?: GetBriefingsParams)=>{
    return [
        "/api/ai/briefings/{persona}",
        params
    ] as const;
};
export function useGetBriefings<TData = {
    data: BriefingResponse;
}>(options: {
    params: GetBriefingsParams;
    query?: Omit<UseQueryOptions<{
        data: BriefingResponse;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: getBriefingsKey(options.params),
        queryFn: ()=>getBriefings(options.params),
        ...options?.query
    });
}
export function useGetBriefingsSuspense<TData = {
    data: BriefingResponse;
}>(options: {
    params: GetBriefingsParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: BriefingResponse;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: getBriefingsKey(options.params),
        queryFn: ()=>getBriefings(options.params),
        ...options?.query
    });
}
export interface RunBriefingsParams {
    persona: string;
}
export const runBriefings = async (params: RunBriefingsParams, options?: RequestInit): Promise<{
    data: BriefingResponse;
}> =>{
    const res = await fetch(`/api/ai/briefings/${params.persona}`, {
        ...options,
        method: "POST"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useRunBriefings(options?: {
    mutation?: UseMutationOptions<{
        data: BriefingResponse;
    }, ApiError, {
        params: RunBriefingsParams;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>runBriefings(vars.params),
        ...options?.mutation
    });
}
export const aiGovernance = async (options?: RequestInit): Promise<{
    data: GovernanceInfo;
}> =>{
    const res = await fetch("/api/ai/governance", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const aiGovernanceKey = ()=>{
    return [
        "/api/ai/governance"
    ] as const;
};
export function useAiGovernance<TData = {
    data: GovernanceInfo;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: GovernanceInfo;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: aiGovernanceKey(),
        queryFn: ()=>aiGovernance(),
        ...options?.query
    });
}
export function useAiGovernanceSuspense<TData = {
    data: GovernanceInfo;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: GovernanceInfo;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: aiGovernanceKey(),
        queryFn: ()=>aiGovernance(),
        ...options?.query
    });
}
export const aiNarrative = async (data: NarrativeRequest, options?: RequestInit): Promise<{
    data: GovernedResponse;
}> =>{
    const res = await fetch("/api/ai/narrative", {
        ...options,
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...options?.headers
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useAiNarrative(options?: {
    mutation?: UseMutationOptions<{
        data: GovernedResponse;
    }, ApiError, NarrativeRequest>;
}) {
    return useMutation({
        mutationFn: (data)=>aiNarrative(data),
        ...options?.mutation
    });
}
export const listAlertAcks = async (options?: RequestInit): Promise<{
    data: AlertAckOut[];
}> =>{
    const res = await fetch("/api/alert-acks", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const listAlertAcksKey = ()=>{
    return [
        "/api/alert-acks"
    ] as const;
};
export function useListAlertAcks<TData = {
    data: AlertAckOut[];
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: AlertAckOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: listAlertAcksKey(),
        queryFn: ()=>listAlertAcks(),
        ...options?.query
    });
}
export function useListAlertAcksSuspense<TData = {
    data: AlertAckOut[];
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: AlertAckOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: listAlertAcksKey(),
        queryFn: ()=>listAlertAcks(),
        ...options?.query
    });
}
export interface AckAlertParams {
    "X-Forwarded-Host"?: string | null;
    "X-Forwarded-Preferred-Username"?: string | null;
    "X-Forwarded-User"?: string | null;
    "X-Forwarded-Email"?: string | null;
    "X-Request-Id"?: string | null;
    "X-Forwarded-Access-Token"?: string | null;
}
export const ackAlert = async (data: AlertAckIn, params?: AckAlertParams, options?: RequestInit): Promise<{
    data: AlertAckOut;
}> =>{
    const res = await fetch("/api/alert-acks", {
        ...options,
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...(params?.["X-Forwarded-Host"] != null && {
                "X-Forwarded-Host": params["X-Forwarded-Host"]
            }),
            ...(params?.["X-Forwarded-Preferred-Username"] != null && {
                "X-Forwarded-Preferred-Username": params["X-Forwarded-Preferred-Username"]
            }),
            ...(params?.["X-Forwarded-User"] != null && {
                "X-Forwarded-User": params["X-Forwarded-User"]
            }),
            ...(params?.["X-Forwarded-Email"] != null && {
                "X-Forwarded-Email": params["X-Forwarded-Email"]
            }),
            ...(params?.["X-Request-Id"] != null && {
                "X-Request-Id": params["X-Request-Id"]
            }),
            ...(params?.["X-Forwarded-Access-Token"] != null && {
                "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"]
            }),
            ...options?.headers
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useAckAlert(options?: {
    mutation?: UseMutationOptions<{
        data: AlertAckOut;
    }, ApiError, {
        params: AckAlertParams;
        data: AlertAckIn;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>ackAlert(vars.data, vars.params),
        ...options?.mutation
    });
}
export interface ListAnnotationsParams {
    persona?: string | null;
}
export const listAnnotations = async (params?: ListAnnotationsParams, options?: RequestInit): Promise<{
    data: AnnotationOut[];
}> =>{
    const searchParams = new URLSearchParams();
    if (params?.persona != null) searchParams.set("persona", String(params?.persona));
    const queryString = searchParams.toString();
    const url = queryString ? `/api/annotations?${queryString}` : "/api/annotations";
    const res = await fetch(url, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const listAnnotationsKey = (params?: ListAnnotationsParams)=>{
    return [
        "/api/annotations",
        params
    ] as const;
};
export function useListAnnotations<TData = {
    data: AnnotationOut[];
}>(options?: {
    params?: ListAnnotationsParams;
    query?: Omit<UseQueryOptions<{
        data: AnnotationOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: listAnnotationsKey(options?.params),
        queryFn: ()=>listAnnotations(options?.params),
        ...options?.query
    });
}
export function useListAnnotationsSuspense<TData = {
    data: AnnotationOut[];
}>(options?: {
    params?: ListAnnotationsParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: AnnotationOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: listAnnotationsKey(options?.params),
        queryFn: ()=>listAnnotations(options?.params),
        ...options?.query
    });
}
export interface AddAnnotationParams {
    "X-Forwarded-Host"?: string | null;
    "X-Forwarded-Preferred-Username"?: string | null;
    "X-Forwarded-User"?: string | null;
    "X-Forwarded-Email"?: string | null;
    "X-Request-Id"?: string | null;
    "X-Forwarded-Access-Token"?: string | null;
}
export const addAnnotation = async (data: AnnotationIn, params?: AddAnnotationParams, options?: RequestInit): Promise<{
    data: AnnotationOut;
}> =>{
    const res = await fetch("/api/annotations", {
        ...options,
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...(params?.["X-Forwarded-Host"] != null && {
                "X-Forwarded-Host": params["X-Forwarded-Host"]
            }),
            ...(params?.["X-Forwarded-Preferred-Username"] != null && {
                "X-Forwarded-Preferred-Username": params["X-Forwarded-Preferred-Username"]
            }),
            ...(params?.["X-Forwarded-User"] != null && {
                "X-Forwarded-User": params["X-Forwarded-User"]
            }),
            ...(params?.["X-Forwarded-Email"] != null && {
                "X-Forwarded-Email": params["X-Forwarded-Email"]
            }),
            ...(params?.["X-Request-Id"] != null && {
                "X-Request-Id": params["X-Request-Id"]
            }),
            ...(params?.["X-Forwarded-Access-Token"] != null && {
                "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"]
            }),
            ...options?.headers
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useAddAnnotation(options?: {
    mutation?: UseMutationOptions<{
        data: AnnotationOut;
    }, ApiError, {
        params: AddAnnotationParams;
        data: AnnotationIn;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>addAnnotation(vars.data, vars.params),
        ...options?.mutation
    });
}
export const cboEadvantageLurkers = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/cbo/eadvantage-lurkers", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const cboEadvantageLurkersKey = ()=>{
    return [
        "/api/cbo/eadvantage-lurkers"
    ] as const;
};
export function useCboEadvantageLurkers<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: cboEadvantageLurkersKey(),
        queryFn: ()=>cboEadvantageLurkers(),
        ...options?.query
    });
}
export function useCboEadvantageLurkersSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: cboEadvantageLurkersKey(),
        queryFn: ()=>cboEadvantageLurkers(),
        ...options?.query
    });
}
export const cboMpfLeakage = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/cbo/mpf-leakage", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const cboMpfLeakageKey = ()=>{
    return [
        "/api/cbo/mpf-leakage"
    ] as const;
};
export function useCboMpfLeakage<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: cboMpfLeakageKey(),
        queryFn: ()=>cboMpfLeakage(),
        ...options?.query
    });
}
export function useCboMpfLeakageSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: cboMpfLeakageKey(),
        queryFn: ()=>cboMpfLeakage(),
        ...options?.query
    });
}
export const cboProspects = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/cbo/prospects", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const cboProspectsKey = ()=>{
    return [
        "/api/cbo/prospects"
    ] as const;
};
export function useCboProspects<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: cboProspectsKey(),
        queryFn: ()=>cboProspects(),
        ...options?.query
    });
}
export function useCboProspectsSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: cboProspectsKey(),
        queryFn: ()=>cboProspects(),
        ...options?.query
    });
}
export const cboUnusedCapacity = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/cbo/unused-capacity", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const cboUnusedCapacityKey = ()=>{
    return [
        "/api/cbo/unused-capacity"
    ] as const;
};
export function useCboUnusedCapacity<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: cboUnusedCapacityKey(),
        queryFn: ()=>cboUnusedCapacity(),
        ...options?.query
    });
}
export function useCboUnusedCapacitySuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: cboUnusedCapacityKey(),
        queryFn: ()=>cboUnusedCapacity(),
        ...options?.query
    });
}
export const cboUtilization = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/cbo/utilization", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const cboUtilizationKey = ()=>{
    return [
        "/api/cbo/utilization"
    ] as const;
};
export function useCboUtilization<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: cboUtilizationKey(),
        queryFn: ()=>cboUtilization(),
        ...options?.query
    });
}
export function useCboUtilizationSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: cboUtilizationKey(),
        queryFn: ()=>cboUtilization(),
        ...options?.query
    });
}
export const cfoAdvancesVsForecast = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/cfo/advances-vs-forecast", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const cfoAdvancesVsForecastKey = ()=>{
    return [
        "/api/cfo/advances-vs-forecast"
    ] as const;
};
export function useCfoAdvancesVsForecast<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: cfoAdvancesVsForecastKey(),
        queryFn: ()=>cfoAdvancesVsForecast(),
        ...options?.query
    });
}
export function useCfoAdvancesVsForecastSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: cfoAdvancesVsForecastKey(),
        queryFn: ()=>cfoAdvancesVsForecast(),
        ...options?.query
    });
}
export const cfoCoSpreads = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/cfo/co-spreads", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const cfoCoSpreadsKey = ()=>{
    return [
        "/api/cfo/co-spreads"
    ] as const;
};
export function useCfoCoSpreads<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: cfoCoSpreadsKey(),
        queryFn: ()=>cfoCoSpreads(),
        ...options?.query
    });
}
export function useCfoCoSpreadsSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: cfoCoSpreadsKey(),
        queryFn: ()=>cfoCoSpreads(),
        ...options?.query
    });
}
export const cfoCoreMissionRatio = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/cfo/core-mission-ratio", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const cfoCoreMissionRatioKey = ()=>{
    return [
        "/api/cfo/core-mission-ratio"
    ] as const;
};
export function useCfoCoreMissionRatio<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: cfoCoreMissionRatioKey(),
        queryFn: ()=>cfoCoreMissionRatio(),
        ...options?.query
    });
}
export function useCfoCoreMissionRatioSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: cfoCoreMissionRatioKey(),
        queryFn: ()=>cfoCoreMissionRatio(),
        ...options?.query
    });
}
export const cfoMbsUnrealized = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/cfo/mbs-unrealized", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const cfoMbsUnrealizedKey = ()=>{
    return [
        "/api/cfo/mbs-unrealized"
    ] as const;
};
export function useCfoMbsUnrealized<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: cfoMbsUnrealizedKey(),
        queryFn: ()=>cfoMbsUnrealized(),
        ...options?.query
    });
}
export function useCfoMbsUnrealizedSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: cfoMbsUnrealizedKey(),
        queryFn: ()=>cfoMbsUnrealized(),
        ...options?.query
    });
}
export interface CfoSofrSensitivityParams {
    bps?: number;
}
export const cfoSofrSensitivity = async (params?: CfoSofrSensitivityParams, options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const searchParams = new URLSearchParams();
    if (params?.bps != null) searchParams.set("bps", String(params?.bps));
    const queryString = searchParams.toString();
    const url = queryString ? `/api/cfo/sofr-sensitivity?${queryString}` : "/api/cfo/sofr-sensitivity";
    const res = await fetch(url, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const cfoSofrSensitivityKey = (params?: CfoSofrSensitivityParams)=>{
    return [
        "/api/cfo/sofr-sensitivity",
        params
    ] as const;
};
export function useCfoSofrSensitivity<TData = {
    data: Rows;
}>(options?: {
    params?: CfoSofrSensitivityParams;
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: cfoSofrSensitivityKey(options?.params),
        queryFn: ()=>cfoSofrSensitivity(options?.params),
        ...options?.query
    });
}
export function useCfoSofrSensitivitySuspense<TData = {
    data: Rows;
}>(options?: {
    params?: CfoSofrSensitivityParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: cfoSofrSensitivityKey(options?.params),
        queryFn: ()=>cfoSofrSensitivity(options?.params),
        ...options?.query
    });
}
export const cioAccessOob = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/cio/access-oob", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const cioAccessOobKey = ()=>{
    return [
        "/api/cio/access-oob"
    ] as const;
};
export function useCioAccessOob<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: cioAccessOobKey(),
        queryFn: ()=>cioAccessOob(),
        ...options?.query
    });
}
export function useCioAccessOobSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: cioAccessOobKey(),
        queryFn: ()=>cioAccessOob(),
        ...options?.query
    });
}
export const cioBiSla = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/cio/bi-sla", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const cioBiSlaKey = ()=>{
    return [
        "/api/cio/bi-sla"
    ] as const;
};
export function useCioBiSla<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: cioBiSlaKey(),
        queryFn: ()=>cioBiSla(),
        ...options?.query
    });
}
export function useCioBiSlaSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: cioBiSlaKey(),
        queryFn: ()=>cioBiSla(),
        ...options?.query
    });
}
export const cioDqExceptions = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/cio/dq-exceptions", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const cioDqExceptionsKey = ()=>{
    return [
        "/api/cio/dq-exceptions"
    ] as const;
};
export function useCioDqExceptions<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: cioDqExceptionsKey(),
        queryFn: ()=>cioDqExceptions(),
        ...options?.query
    });
}
export function useCioDqExceptionsSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: cioDqExceptionsKey(),
        queryFn: ()=>cioDqExceptions(),
        ...options?.query
    });
}
export const cioDualRunCost = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/cio/dual-run-cost", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const cioDualRunCostKey = ()=>{
    return [
        "/api/cio/dual-run-cost"
    ] as const;
};
export function useCioDualRunCost<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: cioDualRunCostKey(),
        queryFn: ()=>cioDualRunCost(),
        ...options?.query
    });
}
export function useCioDualRunCostSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: cioDualRunCostKey(),
        queryFn: ()=>cioDualRunCost(),
        ...options?.query
    });
}
export interface CioLineageParams {
    field: string;
}
export const cioLineage = async (params: CioLineageParams, options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const searchParams = new URLSearchParams();
    if (params.field != null) searchParams.set("field", String(params.field));
    const queryString = searchParams.toString();
    const url = queryString ? `/api/cio/lineage?${queryString}` : "/api/cio/lineage";
    const res = await fetch(url, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const cioLineageKey = (params?: CioLineageParams)=>{
    return [
        "/api/cio/lineage",
        params
    ] as const;
};
export function useCioLineage<TData = {
    data: Rows;
}>(options: {
    params: CioLineageParams;
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: cioLineageKey(options.params),
        queryFn: ()=>cioLineage(options.params),
        ...options?.query
    });
}
export function useCioLineageSuspense<TData = {
    data: Rows;
}>(options: {
    params: CioLineageParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: cioLineageKey(options.params),
        queryFn: ()=>cioLineage(options.params),
        ...options?.query
    });
}
export const cioLineageFields = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/cio/lineage-fields", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const cioLineageFieldsKey = ()=>{
    return [
        "/api/cio/lineage-fields"
    ] as const;
};
export function useCioLineageFields<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: cioLineageFieldsKey(),
        queryFn: ()=>cioLineageFields(),
        ...options?.query
    });
}
export function useCioLineageFieldsSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: cioLineageFieldsKey(),
        queryFn: ()=>cioLineageFields(),
        ...options?.query
    });
}
export const cioModelBacklog = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/cio/model-backlog", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const cioModelBacklogKey = ()=>{
    return [
        "/api/cio/model-backlog"
    ] as const;
};
export function useCioModelBacklog<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: cioModelBacklogKey(),
        queryFn: ()=>cioModelBacklog(),
        ...options?.query
    });
}
export function useCioModelBacklogSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: cioModelBacklogKey(),
        queryFn: ()=>cioModelBacklog(),
        ...options?.query
    });
}
export const croConcentration = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/cro/concentration", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const croConcentrationKey = ()=>{
    return [
        "/api/cro/concentration"
    ] as const;
};
export function useCroConcentration<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: croConcentrationKey(),
        queryFn: ()=>croConcentration(),
        ...options?.query
    });
}
export function useCroConcentrationSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: croConcentrationKey(),
        queryFn: ()=>croConcentration(),
        ...options?.query
    });
}
export interface CroEarlyWarningParams {
    limit?: number;
    refresh?: boolean;
}
export const croEarlyWarning = async (params?: CroEarlyWarningParams, options?: RequestInit): Promise<{
    data: EarlyWarningResponse;
}> =>{
    const searchParams = new URLSearchParams();
    if (params?.limit != null) searchParams.set("limit", String(params?.limit));
    if (params?.refresh != null) searchParams.set("refresh", String(params?.refresh));
    const queryString = searchParams.toString();
    const url = queryString ? `/api/cro/early-warning?${queryString}` : "/api/cro/early-warning";
    const res = await fetch(url, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const croEarlyWarningKey = (params?: CroEarlyWarningParams)=>{
    return [
        "/api/cro/early-warning",
        params
    ] as const;
};
export function useCroEarlyWarning<TData = {
    data: EarlyWarningResponse;
}>(options?: {
    params?: CroEarlyWarningParams;
    query?: Omit<UseQueryOptions<{
        data: EarlyWarningResponse;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: croEarlyWarningKey(options?.params),
        queryFn: ()=>croEarlyWarning(options?.params),
        ...options?.query
    });
}
export function useCroEarlyWarningSuspense<TData = {
    data: EarlyWarningResponse;
}>(options?: {
    params?: CroEarlyWarningParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: EarlyWarningResponse;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: croEarlyWarningKey(options?.params),
        queryFn: ()=>croEarlyWarning(options?.params),
        ...options?.query
    });
}
export const croEarlyWarningScore = async (data: EarlyWarningScoreRequest, options?: RequestInit): Promise<{
    data: EarlyWarningResponse;
}> =>{
    const res = await fetch("/api/cro/early-warning/score", {
        ...options,
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...options?.headers
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useCroEarlyWarningScore(options?: {
    mutation?: UseMutationOptions<{
        data: EarlyWarningResponse;
    }, ApiError, EarlyWarningScoreRequest>;
}) {
    return useMutation({
        mutationFn: (data)=>croEarlyWarningScore(data),
        ...options?.mutation
    });
}
export const croMpfDelinquency = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/cro/mpf-delinquency", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const croMpfDelinquencyKey = ()=>{
    return [
        "/api/cro/mpf-delinquency"
    ] as const;
};
export function useCroMpfDelinquency<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: croMpfDelinquencyKey(),
        queryFn: ()=>croMpfDelinquency(),
        ...options?.query
    });
}
export function useCroMpfDelinquencySuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: croMpfDelinquencyKey(),
        queryFn: ()=>croMpfDelinquency(),
        ...options?.query
    });
}
export const croOcCushion = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/cro/oc-cushion", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const croOcCushionKey = ()=>{
    return [
        "/api/cro/oc-cushion"
    ] as const;
};
export function useCroOcCushion<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: croOcCushionKey(),
        queryFn: ()=>croOcCushion(),
        ...options?.query
    });
}
export function useCroOcCushionSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: croOcCushionKey(),
        queryFn: ()=>croOcCushion(),
        ...options?.query
    });
}
export const croRatingsOverdue = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/cro/ratings-overdue", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const croRatingsOverdueKey = ()=>{
    return [
        "/api/cro/ratings-overdue"
    ] as const;
};
export function useCroRatingsOverdue<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: croRatingsOverdueKey(),
        queryFn: ()=>croRatingsOverdue(),
        ...options?.query
    });
}
export function useCroRatingsOverdueSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: croRatingsOverdueKey(),
        queryFn: ()=>croRatingsOverdue(),
        ...options?.query
    });
}
export interface CurrentUserParams {
    "X-Forwarded-Host"?: string | null;
    "X-Forwarded-Preferred-Username"?: string | null;
    "X-Forwarded-User"?: string | null;
    "X-Forwarded-Email"?: string | null;
    "X-Request-Id"?: string | null;
    "X-Forwarded-Access-Token"?: string | null;
}
export const currentUser = async (params?: CurrentUserParams, options?: RequestInit): Promise<{
    data: User;
}> =>{
    const res = await fetch("/api/current-user", {
        ...options,
        method: "GET",
        headers: {
            ...(params?.["X-Forwarded-Host"] != null && {
                "X-Forwarded-Host": params["X-Forwarded-Host"]
            }),
            ...(params?.["X-Forwarded-Preferred-Username"] != null && {
                "X-Forwarded-Preferred-Username": params["X-Forwarded-Preferred-Username"]
            }),
            ...(params?.["X-Forwarded-User"] != null && {
                "X-Forwarded-User": params["X-Forwarded-User"]
            }),
            ...(params?.["X-Forwarded-Email"] != null && {
                "X-Forwarded-Email": params["X-Forwarded-Email"]
            }),
            ...(params?.["X-Request-Id"] != null && {
                "X-Request-Id": params["X-Request-Id"]
            }),
            ...(params?.["X-Forwarded-Access-Token"] != null && {
                "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"]
            }),
            ...options?.headers
        }
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const currentUserKey = (params?: CurrentUserParams)=>{
    return [
        "/api/current-user",
        params
    ] as const;
};
export function useCurrentUser<TData = {
    data: User;
}>(options?: {
    params?: CurrentUserParams;
    query?: Omit<UseQueryOptions<{
        data: User;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: currentUserKey(options?.params),
        queryFn: ()=>currentUser(options?.params),
        ...options?.query
    });
}
export function useCurrentUserSuspense<TData = {
    data: User;
}>(options?: {
    params?: CurrentUserParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: User;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: currentUserKey(options?.params),
        queryFn: ()=>currentUser(options?.params),
        ...options?.query
    });
}
export const listExamRequests = async (options?: RequestInit): Promise<{
    data: ExamRequestOut[];
}> =>{
    const res = await fetch("/api/exam-requests", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const listExamRequestsKey = ()=>{
    return [
        "/api/exam-requests"
    ] as const;
};
export function useListExamRequests<TData = {
    data: ExamRequestOut[];
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: ExamRequestOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: listExamRequestsKey(),
        queryFn: ()=>listExamRequests(),
        ...options?.query
    });
}
export function useListExamRequestsSuspense<TData = {
    data: ExamRequestOut[];
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: ExamRequestOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: listExamRequestsKey(),
        queryFn: ()=>listExamRequests(),
        ...options?.query
    });
}
export interface CreateExamRequestParams {
    "X-Forwarded-Host"?: string | null;
    "X-Forwarded-Preferred-Username"?: string | null;
    "X-Forwarded-User"?: string | null;
    "X-Forwarded-Email"?: string | null;
    "X-Request-Id"?: string | null;
    "X-Forwarded-Access-Token"?: string | null;
}
export const createExamRequest = async (data: ExamRequestIn, params?: CreateExamRequestParams, options?: RequestInit): Promise<{
    data: ExamRequestOut;
}> =>{
    const res = await fetch("/api/exam-requests", {
        ...options,
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...(params?.["X-Forwarded-Host"] != null && {
                "X-Forwarded-Host": params["X-Forwarded-Host"]
            }),
            ...(params?.["X-Forwarded-Preferred-Username"] != null && {
                "X-Forwarded-Preferred-Username": params["X-Forwarded-Preferred-Username"]
            }),
            ...(params?.["X-Forwarded-User"] != null && {
                "X-Forwarded-User": params["X-Forwarded-User"]
            }),
            ...(params?.["X-Forwarded-Email"] != null && {
                "X-Forwarded-Email": params["X-Forwarded-Email"]
            }),
            ...(params?.["X-Request-Id"] != null && {
                "X-Request-Id": params["X-Request-Id"]
            }),
            ...(params?.["X-Forwarded-Access-Token"] != null && {
                "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"]
            }),
            ...options?.headers
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useCreateExamRequest(options?: {
    mutation?: UseMutationOptions<{
        data: ExamRequestOut;
    }, ApiError, {
        params: CreateExamRequestParams;
        data: ExamRequestIn;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>createExamRequest(vars.data, vars.params),
        ...options?.mutation
    });
}
export interface AddExamItemParams {
    req_id: string;
}
export const addExamItem = async (params: AddExamItemParams, data: ExamPackItemIn, options?: RequestInit): Promise<{
    data: ExamPackItemOut;
}> =>{
    const res = await fetch(`/api/exam-requests/${params.req_id}/items`, {
        ...options,
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...options?.headers
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useAddExamItem(options?: {
    mutation?: UseMutationOptions<{
        data: ExamPackItemOut;
    }, ApiError, {
        params: AddExamItemParams;
        data: ExamPackItemIn;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>addExamItem(vars.params, vars.data),
        ...options?.mutation
    });
}
export const freshness = async (options?: RequestInit): Promise<{
    data: Freshness;
}> =>{
    const res = await fetch("/api/freshness", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const freshnessKey = ()=>{
    return [
        "/api/freshness"
    ] as const;
};
export function useFreshness<TData = {
    data: Freshness;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Freshness;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: freshnessKey(),
        queryFn: ()=>freshness(),
        ...options?.query
    });
}
export function useFreshnessSuspense<TData = {
    data: Freshness;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Freshness;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: freshnessKey(),
        queryFn: ()=>freshness(),
        ...options?.query
    });
}
export interface GenieAgentAskParams {
    persona: string;
}
export const genieAgentAsk = async (params: GenieAgentAskParams, data: GenieAgentRequest, options?: RequestInit): Promise<{
    data: unknown;
}> =>{
    const res = await fetch(`/api/genie-agent/${params.persona}`, {
        ...options,
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...options?.headers
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useGenieAgentAsk(options?: {
    mutation?: UseMutationOptions<{
        data: unknown;
    }, ApiError, {
        params: GenieAgentAskParams;
        data: GenieAgentRequest;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>genieAgentAsk(vars.params, vars.data),
        ...options?.mutation
    });
}
export interface GenieVizParams {
    persona: string;
    conversation_id: string;
    message_id: string;
    attachment_id: string;
}
export const genieViz = async (params: GenieVizParams, options?: RequestInit): Promise<{
    data: unknown;
}> =>{
    const res = await fetch(`/api/genie-viz/${params.persona}/${params.conversation_id}/${params.message_id}/${params.attachment_id}`, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const genieVizKey = (params?: GenieVizParams)=>{
    return [
        "/api/genie-viz/{persona}/{conversation_id}/{message_id}/{attachment_id}",
        params
    ] as const;
};
export function useGenieViz<TData = {
    data: unknown;
}>(options: {
    params: GenieVizParams;
    query?: Omit<UseQueryOptions<{
        data: unknown;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: genieVizKey(options.params),
        queryFn: ()=>genieViz(options.params),
        ...options?.query
    });
}
export function useGenieVizSuspense<TData = {
    data: unknown;
}>(options: {
    params: GenieVizParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: unknown;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: genieVizKey(options.params),
        queryFn: ()=>genieViz(options.params),
        ...options?.query
    });
}
export interface GenieAskParams {
    persona: string;
}
export const genieAsk = async (params: GenieAskParams, data: GenieRequest, options?: RequestInit): Promise<{
    data: GenieResponse;
}> =>{
    const res = await fetch(`/api/genie/${params.persona}`, {
        ...options,
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...options?.headers
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useGenieAsk(options?: {
    mutation?: UseMutationOptions<{
        data: GenieResponse;
    }, ApiError, {
        params: GenieAskParams;
        data: GenieRequest;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>genieAsk(vars.params, vars.data),
        ...options?.mutation
    });
}
export const missionAhpFunnel = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/mission/ahp-funnel", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const missionAhpFunnelKey = ()=>{
    return [
        "/api/mission/ahp-funnel"
    ] as const;
};
export function useMissionAhpFunnel<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: missionAhpFunnelKey(),
        queryFn: ()=>missionAhpFunnel(),
        ...options?.query
    });
}
export function useMissionAhpFunnelSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: missionAhpFunnelKey(),
        queryFn: ()=>missionAhpFunnel(),
        ...options?.query
    });
}
export const missionPledge = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/mission/pledge", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const missionPledgeKey = ()=>{
    return [
        "/api/mission/pledge"
    ] as const;
};
export function useMissionPledge<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: missionPledgeKey(),
        queryFn: ()=>missionPledge(),
        ...options?.query
    });
}
export function useMissionPledgeSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: missionPledgeKey(),
        queryFn: ()=>missionPledge(),
        ...options?.query
    });
}
export const missionSubsidyEfficiency = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/mission/subsidy-efficiency", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const missionSubsidyEfficiencyKey = ()=>{
    return [
        "/api/mission/subsidy-efficiency"
    ] as const;
};
export function useMissionSubsidyEfficiency<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: missionSubsidyEfficiencyKey(),
        queryFn: ()=>missionSubsidyEfficiency(),
        ...options?.query
    });
}
export function useMissionSubsidyEfficiencySuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: missionSubsidyEfficiencyKey(),
        queryFn: ()=>missionSubsidyEfficiency(),
        ...options?.query
    });
}
export const missionUnitsByTier = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/mission/units-by-tier", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const missionUnitsByTierKey = ()=>{
    return [
        "/api/mission/units-by-tier"
    ] as const;
};
export function useMissionUnitsByTier<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: missionUnitsByTierKey(),
        queryFn: ()=>missionUnitsByTier(),
        ...options?.query
    });
}
export function useMissionUnitsByTierSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: missionUnitsByTierKey(),
        queryFn: ()=>missionUnitsByTier(),
        ...options?.query
    });
}
export const overviewAlerts = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/overview/alerts", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const overviewAlertsKey = ()=>{
    return [
        "/api/overview/alerts"
    ] as const;
};
export function useOverviewAlerts<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: overviewAlertsKey(),
        queryFn: ()=>overviewAlerts(),
        ...options?.query
    });
}
export function useOverviewAlertsSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: overviewAlertsKey(),
        queryFn: ()=>overviewAlerts(),
        ...options?.query
    });
}
export const overviewDistrict = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/overview/district", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const overviewDistrictKey = ()=>{
    return [
        "/api/overview/district"
    ] as const;
};
export function useOverviewDistrict<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: overviewDistrictKey(),
        queryFn: ()=>overviewDistrict(),
        ...options?.query
    });
}
export function useOverviewDistrictSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: overviewDistrictKey(),
        queryFn: ()=>overviewDistrict(),
        ...options?.query
    });
}
export const overviewKpis = async (options?: RequestInit): Promise<{
    data: Rows;
}> =>{
    const res = await fetch("/api/overview/kpis", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const overviewKpisKey = ()=>{
    return [
        "/api/overview/kpis"
    ] as const;
};
export function useOverviewKpis<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: overviewKpisKey(),
        queryFn: ()=>overviewKpis(),
        ...options?.query
    });
}
export function useOverviewKpisSuspense<TData = {
    data: Rows;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: Rows;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: overviewKpisKey(),
        queryFn: ()=>overviewKpis(),
        ...options?.query
    });
}
export const version = async (options?: RequestInit): Promise<{
    data: VersionOut;
}> =>{
    const res = await fetch("/api/version", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const versionKey = ()=>{
    return [
        "/api/version"
    ] as const;
};
export function useVersion<TData = {
    data: VersionOut;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: VersionOut;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: versionKey(),
        queryFn: ()=>version(),
        ...options?.query
    });
}
export function useVersionSuspense<TData = {
    data: VersionOut;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: VersionOut;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: versionKey(),
        queryFn: ()=>version(),
        ...options?.query
    });
}
export const listWatchlist = async (options?: RequestInit): Promise<{
    data: WatchlistItemOut[];
}> =>{
    const res = await fetch("/api/watchlist", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const listWatchlistKey = ()=>{
    return [
        "/api/watchlist"
    ] as const;
};
export function useListWatchlist<TData = {
    data: WatchlistItemOut[];
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: WatchlistItemOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: listWatchlistKey(),
        queryFn: ()=>listWatchlist(),
        ...options?.query
    });
}
export function useListWatchlistSuspense<TData = {
    data: WatchlistItemOut[];
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: WatchlistItemOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: listWatchlistKey(),
        queryFn: ()=>listWatchlist(),
        ...options?.query
    });
}
export interface AddWatchlistParams {
    "X-Forwarded-Host"?: string | null;
    "X-Forwarded-Preferred-Username"?: string | null;
    "X-Forwarded-User"?: string | null;
    "X-Forwarded-Email"?: string | null;
    "X-Request-Id"?: string | null;
    "X-Forwarded-Access-Token"?: string | null;
}
export const addWatchlist = async (data: WatchlistIn, params?: AddWatchlistParams, options?: RequestInit): Promise<{
    data: WatchlistItemOut;
}> =>{
    const res = await fetch("/api/watchlist", {
        ...options,
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...(params?.["X-Forwarded-Host"] != null && {
                "X-Forwarded-Host": params["X-Forwarded-Host"]
            }),
            ...(params?.["X-Forwarded-Preferred-Username"] != null && {
                "X-Forwarded-Preferred-Username": params["X-Forwarded-Preferred-Username"]
            }),
            ...(params?.["X-Forwarded-User"] != null && {
                "X-Forwarded-User": params["X-Forwarded-User"]
            }),
            ...(params?.["X-Forwarded-Email"] != null && {
                "X-Forwarded-Email": params["X-Forwarded-Email"]
            }),
            ...(params?.["X-Request-Id"] != null && {
                "X-Request-Id": params["X-Request-Id"]
            }),
            ...(params?.["X-Forwarded-Access-Token"] != null && {
                "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"]
            }),
            ...options?.headers
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useAddWatchlist(options?: {
    mutation?: UseMutationOptions<{
        data: WatchlistItemOut;
    }, ApiError, {
        params: AddWatchlistParams;
        data: WatchlistIn;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>addWatchlist(vars.data, vars.params),
        ...options?.mutation
    });
}
export interface RemoveWatchlistParams {
    item_id: string;
}
export const removeWatchlist = async (params: RemoveWatchlistParams, options?: RequestInit): Promise<{
    data: unknown;
}> =>{
    const res = await fetch(`/api/watchlist/${params.item_id}`, {
        ...options,
        method: "DELETE"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useRemoveWatchlist(options?: {
    mutation?: UseMutationOptions<{
        data: unknown;
    }, ApiError, {
        params: RemoveWatchlistParams;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>removeWatchlist(vars.params),
        ...options?.mutation
    });
}
