import { ClientAtlasApp } from "@/frontend/clientatlas-app";

export default async function ProductPage({
  params
}: Readonly<{ params: Promise<{ view?: string[] }> }>) {
  const { view = [] } = await params;
  return <ClientAtlasApp route={view.join("/") || "overview"} />;
}
