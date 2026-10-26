import { Suspense } from 'react';
import { TemplateDetail } from '../../../components/templates';
export const metadata={title:'模板结构详情'};
export default async function TemplatePage({params}:{params:Promise<{id:string}>}){const{id}=await params;return <Suspense fallback={<div className="page-state">正在加载模板详情…</div>}><TemplateDetail id={id}/></Suspense>;}
