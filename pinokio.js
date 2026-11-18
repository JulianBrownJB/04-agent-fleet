module.exports = {
  version: "2.0",
  title: "Autonomous Multi-Agent Task Fleet",
  description: "A three-stage multi-agent mission pipeline across three departments.",
  menu: async (kernel, info) => {
    let installed = info.exists("env")
    let running = info.running("start.json")
    if (installed) {
      if (running) {
        let local = info.local("start.json")
        if (local && local.url) {
          return [
            { icon: "fa-solid fa-rocket", text: "Open Web UI", href: local.url, target: "_blank" },
            { icon: "fa-solid fa-terminal", text: "Terminal", href: "start.json", target: "_blank" }
          ]
        } else {
          return [{ icon: "fa-solid fa-terminal", text: "Terminal", href: "start.json", target: "_blank" }]
        }
      } else {
        return [
          { icon: "fa-solid fa-play", text: "Start", href: "start.json", params: { fullscreen: true } },
          { icon: "fa-solid fa-terminal", text: "Terminal", href: "start.json", target: "_blank" }
        ]
      }
    } else {
      return [{ icon: "fa-solid fa-plug", text: "Install", href: "install.json", params: { fullscreen: true } }]
    }
  }
}
