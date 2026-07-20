import { a as require_react, o as __toESM, t as require_jsx_runtime } from "../index.js";
//#region app/page.tsx
var import_react = /* @__PURE__ */ __toESM(require_react(), 1);
var import_jsx_runtime = require_jsx_runtime();
var data = {
	小红书: {
		mark: "X",
		role: "沉淀高质量关注",
		signal: "收藏与涨粉质量最高",
		risk: "完播率仍低",
		metrics: [
			["曝光", "2.4 万"],
			["观看", "5,317"],
			["封面点击", "8.5%"],
			["平均观看", "39 秒"],
			["完播", "1.9%"],
			["涨粉", "+70"]
		],
		insight: "赞 205、收藏 159、分享 18。观众愿意把内容留下，说明“可收藏的硬核知识”已经形成正反馈。",
		action: "用 45-90 秒单问题版本，把核心答案提前到 15-25 秒内。",
		base: {
			plays: 5317,
			completion: 1.9,
			interaction: 7.3,
			followers: 70
		}
	},
	抖音: {
		mark: "D",
		role: "测试爆款钩子与选题",
		signal: "播放、互动、涨粉高于同类",
		risk: "完播低于同类",
		metrics: [
			["近 7 日播放", "5,345"],
			["互动率", "3.1%"],
			["同类互动", "2.6%"],
			["完播", "2.7%"],
			["同类完播", "6.2%"],
			["净涨粉", "+29"]
		],
		insight: "有 831 次作品搜索。“明确对象 + 明确结果”的题材，比抽象芯片讲解更容易进入大众视野。",
		action: "用 30-60 秒强钩子版本，首秒先给冲突或反常识结果。",
		base: {
			plays: 5345,
			completion: 2.7,
			interaction: 3.1,
			followers: 29
		}
	},
	快手: {
		mark: "K",
		role: "短版本分发实验",
		signal: "播放与平台助推最强",
		risk: "曝光没有转成互动和涨粉",
		metrics: [
			["近 30 日播放", "3.9 万"],
			["作品数", "19"],
			["完播", "1.4%"],
			["点赞", "54"],
			["分享", "0"],
			["净涨粉", "+18"]
		],
		insight: "近 7 日播放超过 90.7% 同类，并获得 6,243 次额外助推；但互动、分享和作品涨粉仍弱。",
		action: "先只发 30-60 秒、口语化且结论更早出现的版本，再验证互动转化。",
		base: {
			plays: 39e3,
			completion: 1.4,
			interaction: .17,
			followers: 18
		}
	}
};
var format = new Intl.NumberFormat("zh-CN");
function delta(value, base) {
	if (!value || !base) return "—";
	const d = (value - base) / base * 100;
	return `${d >= 0 ? "+" : ""}${d.toFixed(0)}%`;
}
function Home() {
	const [active, setActive] = (0, import_react.useState)("小红书");
	const [records, setRecords] = (0, import_react.useState)([]);
	const [ready, setReady] = (0, import_react.useState)(false);
	const [notice, setNotice] = (0, import_react.useState)("");
	(0, import_react.useEffect)(() => {
		const raw = localStorage.getItem("yinghe-review-records");
		if (raw) try {
			setRecords(JSON.parse(raw));
		} catch {
			localStorage.removeItem("yinghe-review-records");
		}
		setReady(true);
	}, []);
	(0, import_react.useEffect)(() => {
		if (ready) localStorage.setItem("yinghe-review-records", JSON.stringify(records));
	}, [records, ready]);
	const selected = data[active];
	const list = (0, import_react.useMemo)(() => records.filter((item) => item.platform === active).slice().reverse(), [records, active]);
	const add = (event) => {
		event.preventDefault();
		const form = new FormData(event.currentTarget);
		setRecords((items) => [...items, {
			id: crypto.randomUUID(),
			platform: form.get("platform"),
			period: String(form.get("period") || "未命名周期"),
			plays: Number(form.get("plays") || 0),
			completion: Number(form.get("completion") || 0),
			interaction: Number(form.get("interaction") || 0),
			followers: Number(form.get("followers") || 0),
			note: String(form.get("note") || "")
		}]);
		event.currentTarget.reset();
		setNotice("已保存到当前浏览器，下次打开本页仍可继续对比。");
	};
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("main", { children: [
		/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("header", {
			className: "site-header",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("a", {
				className: "brand",
				href: "#top",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
					className: "brand-mark",
					children: "硬"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "硬核视界" })]
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("nav", { children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
					href: "#baseline",
					children: "基线"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
					href: "#strategy",
					children: "策略"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
					href: "#review",
					children: "复盘记录"
				})
			] })]
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
			className: "hero",
			id: "top",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "hero-copy",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "eyebrow",
						children: "MULTI-PLATFORM REVIEW · 2026.07.17"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("h1", { children: [
						"别只看播放量，",
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("br", {}),
						"看清内容在哪一段掉了。"
					] }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "hero-text",
						children: "这是硬核视界的首期多平台数据基线。用同一套链路看曝光、留存、互动与涨粉，下一次复盘就能知道该加码什么、该停止什么。"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
						className: "hero-note",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {}), "当前优先：短版本重剪，而非继续增加十分钟完整版数量"]
					})
				]
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "signal-board",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "signal-top",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "本期判断" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("b", { children: "01 / 03" })]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "signal-line" }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "signal-grid",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("small", { children: "初始分发" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("strong", { children: "已验证" })] }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("small", { children: "观看留存" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("strong", { children: "待重做" })] }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("small", { children: "互动转化" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("strong", { children: "平台分化" })] }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("small", { children: "下一步" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("strong", { children: "一源多剪" })] })
						]
					})
				]
			})]
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
			className: "section",
			id: "baseline",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "section-heading",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "eyebrow",
							children: "01 / BASELINE"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", { children: "首期数据基线" }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { children: "后台统计周期不完全一致，以下用于观察结构和变化趋势，不用于绝对播放量排名。" })
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "platform-tabs",
					role: "tablist",
					children: Object.keys(data).map((platform) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("button", {
						className: active === platform ? "platform-tab active" : "platform-tab",
						onClick: () => setActive(platform),
						role: "tab",
						"aria-selected": active === platform,
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: data[platform].mark }), platform]
					}, platform))
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("article", {
					className: "platform-panel",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "platform-summary",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
								className: "marker-large",
								children: selected.mark
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
									className: "panel-kicker",
									children: [active, " · 当前角色"]
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", { children: selected.role }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { children: selected.insight })
							] })]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "metric-grid",
							children: selected.metrics.map(([label, value]) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "metric",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: label }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("b", { children: value })]
							}, label))
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "panel-footer",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "强信号" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("b", { children: selected.signal })] }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "要解决" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("b", { children: selected.risk })] }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "next-action",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "下一步" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("b", { children: selected.action })]
								})
							]
						})
					]
				})
			]
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)("section", {
			className: "chain-section",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "section chain-inner",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "section-heading compact",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "eyebrow",
						children: "02 / CONTENT CHAIN"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", { children: "三个平台共同卡在“进入内容之后”" })]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "chain",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "chain-step good",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "01" }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", { children: "被看见" }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { children: "题材、标题和封面能够取得初始分发。" })
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "chain-arrow",
							children: "→"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "chain-step warning",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "02" }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", { children: "看下去" }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { children: "十分钟长版平均仅看 15-47 秒，答案出现太晚。" })
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "chain-arrow",
							children: "→"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "chain-step split",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "03" }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", { children: "留下来" }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { children: "小红书已形成收藏和关注；抖音、快手需提升转化。" })
							]
						})
					]
				})]
			})
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
			className: "section strategy",
			id: "strategy",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "section-heading",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "eyebrow",
						children: "03 / PLAYBOOK"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", { children: "下一轮：把一条长片拆成多个独立答案" }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { children: "先用连续 10-15 条短版本验证结构，再决定哪个题材值得扩展成长内容。" })
				]
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "playbook-layout",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("article", {
					className: "sequence-card",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "card-label",
						children: "45-60 秒通用结构"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("ol", { children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "0-2s" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("b", { children: "先给冲突" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { children: "“SR-71 为什么能让导弹追不上？”" })] })] }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "2-10s" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("b", { children: "说明重要性" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { children: "告诉观众：这不是快，而是拦截窗口被压缩。" })] })] }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "10-45s" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("b", { children: "只讲一个机制" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { children: "用一个动态过程或结构图解决一个问题。" })] })] }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "结尾" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("b", { children: "给结论，留下一问" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { children: "“下一条讲它为什么飞到机身会发烫。”" })] })] })
					] })]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("article", {
					className: "test-card",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "card-label",
						children: "题材测试优先级"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "topic-list",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "01" }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("b", { children: "军工装备" }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { children: "战机、航母、潜艇、导弹防御。工程画面强、冲突明确。" })
							] }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "02" }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("b", { children: "大工程与全球影响" }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { children: "航线、运河、超级机械。先讲结果，再讲原理。" })
							] }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "03" }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("b", { children: "芯片与 AI" }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { children: "必须换成生活问题和动态图，不从抽象定义讲起。" })
							] })
						]
					})]
				})]
			})]
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
			className: "section review-section",
			id: "review",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "section-heading",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "eyebrow",
						children: "04 / NEXT REVIEW"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", { children: "记录下一次测试" }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { children: "数据仅保存在当前浏览器。每次尽量使用相同统计周期，并一次只验证一到两个变量。" })
				]
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "review-layout",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
					className: "review-form",
					onSubmit: add,
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "form-row two",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", { children: ["平台", /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("select", {
								name: "platform",
								defaultValue: "小红书",
								children: [
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", { children: "小红书" }),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", { children: "抖音" }),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", { children: "快手" })
								]
							})] }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", { children: ["复盘周期", /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
								name: "period",
								placeholder: "例如：2026.07.18-07.24",
								required: true
							})] })]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "form-row four",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", { children: ["播放/观看", /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
									name: "plays",
									type: "number",
									min: "0",
									placeholder: "0"
								})] }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", { children: ["完播率 %", /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
									name: "completion",
									type: "number",
									min: "0",
									step: "0.01",
									placeholder: "0"
								})] }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", { children: ["互动率 %", /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
									name: "interaction",
									type: "number",
									min: "0",
									step: "0.01",
									placeholder: "0"
								})] }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", { children: ["新增粉丝", /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
									name: "followers",
									type: "number",
									min: "0",
									placeholder: "0"
								})] })
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", { children: ["本次变量与观察", /* @__PURE__ */ (0, import_jsx_runtime.jsx)("textarea", {
							name: "note",
							placeholder: "例如：将答案提前到第 2 秒；收藏提升，但完播未变。",
							rows: 3
						})] }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "form-action",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
								type: "submit",
								children: "保存本次记录"
							}), notice && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: notice })]
						})
					]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("aside", {
					className: "comparison-card",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "comparison-head",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { children: "当前查看" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("h3", { children: [active, " 对比"] })] }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
							onClick: () => setActive("小红书"),
							children: "回到基线"
						})]
					}), list.length === 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "empty-state",
						children: [
							"还没有 ",
							active,
							" 的新记录。填写左侧表单后，这里会自动与首期基线对比。"
						]
					}) : list.map((record) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "record",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "record-title",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("b", { children: record.period }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
									onClick: () => setRecords((items) => items.filter((item) => item.id !== record.id)),
									children: "删除"
								})]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "record-metrics",
								children: [
									/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { children: [
										"播放 ",
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)("b", { children: format.format(record.plays) }),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)("em", { children: delta(record.plays, selected.base.plays) })
									] }),
									/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { children: [
										"完播 ",
										/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("b", { children: [record.completion, "%"] }),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)("em", { children: delta(record.completion, selected.base.completion) })
									] }),
									/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { children: [
										"互动 ",
										/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("b", { children: [record.interaction, "%"] }),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)("em", { children: delta(record.interaction, selected.base.interaction) })
									] }),
									/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { children: [
										"涨粉 ",
										/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("b", { children: ["+", record.followers] }),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)("em", { children: delta(record.followers, selected.base.followers) })
									] })
								]
							}),
							record.note && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { children: record.note })
						]
					}, record.id))]
				})]
			})]
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("footer", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "硬核视界 / 多平台复盘看板" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "基线数据来自 2026 年 7 月 17 日前后平台后台截图" })] })
	] });
}
//#endregion
export { Home as default };
