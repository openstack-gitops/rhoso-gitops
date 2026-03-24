{{/*
Namespace for Argo CD Application CRs (metadata.namespace).
Pass root context ($) from inside range.
*/}}
{{- define "rhoso-apps.applicationNamespace" -}}
{{- default "openshift-gitops" .Values.applicationNamespace | quote -}}
{{- end }}

{{/*
Default Kubernetes API server URL for spec.destination.server.
Pass root context ($) from inside range.
*/}}
{{- define "rhoso-apps.destinationServer" -}}
{{- default "https://kubernetes.default.svc" .Values.destinationServer | quote -}}
{{- end }}

{{/*
Argo CD AppProject name; empty string in values maps to "default".
Pass dict with key "app" (per-application values map).
*/}}
{{- define "rhoso-apps.argocdProject" -}}
{{- $app := .app -}}
{{- default "default" $app.project | quote -}}
{{- end }}

{{/*
Repository path under spec.source.path.
*/}}
{{- define "rhoso-apps.sourcePath" -}}
{{- $app := .app -}}
{{- default "." $app.path | quote -}}
{{- end }}

{{/*
Git revision, branch, or tag for spec.source.targetRevision.
*/}}
{{- define "rhoso-apps.targetRevision" -}}
{{- $app := .app -}}
{{- default "HEAD" $app.targetRevision | quote -}}
{{- end }}

{{/*
argocd.argoproj.io/sync-wave annotation; omitted in values defaults to "0".
Pass dict with key "app" (per-application values map).
*/}}
{{- define "rhoso-apps.syncWave" -}}
{{- $app := .app -}}
{{- default "0" $app.syncWave | quote -}}
{{- end }}

{{/*
Optional spec.source.kustomize (Argo CD Kustomize overrides).
Pass dict with key "app" (per-application values map). Omitted if unset, non-map, or empty map.
*/}}
{{- define "rhoso-apps.sourceKustomize" -}}
{{- $app := .app -}}
{{- $k := $app.kustomize | default dict }}
{{- if not (kindIs "map" $k) }}
{{- $k = dict }}
{{- end }}
{{- if not (empty $k) }}
    kustomize:
{{ toYaml $k | nindent 6 }}
{{- end }}
{{- end }}

{{/*
Build spec.syncPolicy; emit block or nothing.
If syncPolicy is a non-empty map, it is the sole source (top-level syncOptions is ignored).
If syncPolicy is absent or empty, top-level syncOptions is merged in as spec.syncPolicy.syncOptions.
Pass dict with key "app" (per-application values map).
*/}}
{{- define "rhoso-apps.syncPolicySpec" -}}
{{- $app := .app -}}
{{- $merged := $app.syncPolicy | default dict }}
{{- if not (kindIs "map" $merged) }}
{{- $merged = dict }}
{{- end }}
{{- if not (empty $merged) }}
  syncPolicy:
{{ toYaml $merged | indent 4 }}
{{- else if and $app.syncOptions (not (empty $app.syncOptions)) }}
{{- $only := dict "syncOptions" $app.syncOptions }}
  syncPolicy:
{{ toYaml $only | indent 4 }}
{{- end }}
{{- end }}

{{/*
Argo CD Application metadata.finalizers (resources finalizer: background vs foreground).
Omitted finalizers default to background deletion.
Pass dict with key "app" (per-application values map).
*/}}
{{- define "rhoso-apps.applicationFinalizers" -}}
{{- $app := .app -}}
{{- $f := default (list "resources-finalizer.argocd.argoproj.io/background") $app.finalizers }}
{{- toYaml $f -}}
{{- end }}
