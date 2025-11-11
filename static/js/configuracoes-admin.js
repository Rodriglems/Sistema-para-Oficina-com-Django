  // Gerenciamento de tabs
  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const tabId = btn.dataset.tab;

        // Remove active de todos os botões e conteúdos
        document
          .querySelectorAll(".tab-btn")
          .forEach((b) => b.classList.remove("active"));
        document
          .querySelectorAll(".tab-content")
          .forEach((c) => c.classList.remove("active"));

        // Adiciona active ao botão clicado e seu conteúdo
        btn.classList.add("active");
        document.getElementById(tabId).classList.add("active");
      });
    });
  });

  // Funções para os botões
  function showModal(type) {
    alert(
      "Modal para " +
        type +
        " em desenvolvimento. Esta funcionalidade será implementada em breve."
    );
  }

  function exportUsers() {
    if (confirm("Deseja exportar a lista de usuários para CSV?")) {
      window.location.href = '{% url "export_users" %}';
    }
  }

  // Event listeners para botões de serviço
  document.addEventListener("DOMContentLoaded", function () {
    // Botões de editar serviço
    document.querySelectorAll(".edit-service-btn").forEach((btn) => {
      btn.addEventListener("click", function () {
        const serviceId = this.getAttribute("data-service-id");
        alert("Edição de serviço ID: " + serviceId + " em desenvolvimento.");
      });
    });

    // Botões de toggle serviço
    document.querySelectorAll(".toggle-service-btn").forEach((btn) => {
      btn.addEventListener("click", function () {
        const serviceId = this.getAttribute("data-service-id");
        if (confirm("Confirma a alteração do status deste serviço?")) {
          alert("Status alterado com sucesso!");
        }
      });
    });
  });


  function viewSecurityLogs() {
    window.open("/admin/security-logs/", "_blank");
  }

  // Funcionalidades de Tema
  document.addEventListener("DOMContentLoaded", function () {
    // Seleção de tema
    document.querySelectorAll(".theme-option").forEach((option) => {
      option.addEventListener("click", function () {
        // Remove seleção anterior
        document
          .querySelectorAll(".theme-option")
          .forEach((opt) => opt.classList.remove("selected"));
        // Adiciona seleção atual
        this.classList.add("selected");
        // Marca o radio button
        this.querySelector('input[type="radio"]').checked = true;

        // Aplica preview do tema
        const theme = this.dataset.theme;
        applyThemePreview(theme);
      });
    });

    // Mudança de cores personalizadas
    document.querySelectorAll('input[type="color"]').forEach((input) => {
      input.addEventListener("change", function () {
        const preview = document.getElementById(
          "preview-" + this.name.replace("cor_", "")
        );
        if (preview) {
          preview.style.backgroundColor = this.value;
        }
        updateLivePreview();
      });
    });
  });

  function applyThemePreview(theme) {
    const themeColors = {
      azul: { primary: "#3b8d9e", secondary: "#2e7a87", accent: "#17a2b8" },
      verde: { primary: "#28a745", secondary: "#20c997", accent: "#17a2b8" },
      laranja: { primary: "#ff6b35", secondary: "#f4623a", accent: "#fd7e14" },
      roxo: { primary: "#6f42c1", secondary: "#563d7c", accent: "#e83e8c" },
      escuro: { primary: "#343a40", secondary: "#495057", accent: "#6c757d" },
    };

    if (themeColors[theme]) {
      document.documentElement.style.setProperty(
        "--primary-color",
        themeColors[theme].primary
      );
      document.documentElement.style.setProperty(
        "--secondary-color",
        themeColors[theme].secondary
      );
      document.documentElement.style.setProperty(
        "--accent-color",
        themeColors[theme].accent
      );
    }
  }

  function updateLivePreview() {
    const corPrimaria = document.getElementById("cor_primaria").value;
    const corSecundaria = document.getElementById("cor_secundaria").value;
    const corAcento = document.getElementById("cor_acento").value;

    document.documentElement.style.setProperty("--primary-color", corPrimaria);
    document.documentElement.style.setProperty(
      "--secondary-color",
      corSecundaria
    );
    document.documentElement.style.setProperty("--accent-color", corAcento);
  }

  // Funcionalidades de Segurança
  function cleanupData(type) {
    const messages = {
      agendamentos:
        "Confirma a limpeza dos agendamentos antigos? Esta ação não pode ser desfeita.",
      logs: "Confirma a limpeza dos logs do sistema? Esta ação não pode ser desfeita.",
      temp: "Confirma a limpeza dos arquivos temporários?",
    };

    if (confirm(messages[type])) {
      showNotification(" Limpeza de " + type + " iniciada!", "info");

      // Fazer requisição AJAX para limpar dados
      fetch('{% url "limpar_dados_sistema" %}', {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")
            .value,
        },
        body: "tipo=" + encodeURIComponent(type),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            showNotification("✅ " + data.message, "success");
          } else {
            showNotification(
              "❌ " + (data.error || "Erro durante a limpeza"),
              "error"
            );
          }
        })
        .catch((error) => {
          showNotification("❌ Erro de conexão: " + error.message, "error");
        });
    }
  }

  function resetAllData() {
    const confirmation1 = confirm(
      "⚠️ ATENÇÃO! Esta ação irá APAGAR TODOS os dados do sistema!\n\nTem certeza que deseja continuar?"
    );

    if (confirmation1) {
      const confirmation2 = confirm(
        "🚨 ÚLTIMA CONFIRMAÇÃO!\n\nEsta ação é IRREVERSÍVEL e apagará:\n- Todos os clientes\n- Todos os agendamentos\n- Todos os mecânicos\n- Todas as ordens de serviço\n\nClique OK para continuar:"
      );

      if (confirmation2) {
        const finalConfirm = prompt(
          'Digite "CONFIRMAR RESET" para prosseguir:'
        );
        if (finalConfirm === "CONFIRMAR RESET") {
          showNotification(
            "💥 Reset do sistema iniciado... Aguarde!",
            "warning"
          );

          // Fazer requisição AJAX para reset total
          fetch('{% url "limpar_dados_sistema" %}', {
            method: "POST",
            headers: {
              "Content-Type": "application/x-www-form-urlencoded",
              "X-CSRFToken": document.querySelector(
                "[name=csrfmiddlewaretoken]"
              ).value,
            },
            body:
              "tipo=reset_total&confirmacao=" +
              encodeURIComponent(finalConfirm),
          })
            .then((response) => response.json())
            .then((data) => {
              if (data.success) {
                showNotification("💥 " + data.message, "success");
                setTimeout(() => {
                  window.location.reload();
                }, 3000);
              } else {
                showNotification(
                  "❌ " + (data.error || "Erro durante o reset"),
                  "error"
                );
              }
            })
            .catch((error) => {
              showNotification("❌ Erro de conexão: " + error.message, "error");
            });
        } else {
          showNotification(
            "❌ Reset cancelado - confirmação incorreta.",
            "info"
          );
        }
      }
    }
  }

  // Validação de senha
  document.addEventListener("DOMContentLoaded", function () {
    const passwordForm = document.querySelector(".password-form");
    if (passwordForm) {
      passwordForm.addEventListener("submit", function (e) {
        const novaSenha = document.getElementById("nova_senha").value;
        const confirmarSenha = document.getElementById("confirmar_senha").value;

        if (novaSenha !== confirmarSenha) {
          e.preventDefault();
          showNotification("❌ As senhas não coincidem!", "error");
          return;
        }

        if (novaSenha.length < 8) {
          e.preventDefault();
          showNotification(
            "❌ A senha deve ter pelo menos 8 caracteres!",
            "error"
          );
          return;
        }

        showNotification("🔐 Alterando senha...", "info");
      });
    }
  });

  function showNotification(message, type = "info") {
    const colors = {
      success: "#28a745",
      error: "#dc3545",
      warning: "#ffc107",
      info: "#17a2b8",
    };

    const notification = document.createElement("div");
    notification.textContent = message;
    notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: ${colors[type]};
    color: white;
    padding: 15px 25px;
    border-radius: 8px;
    z-index: 1000;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    animation: slideInRight 0.5s ease-out, slideOutRight 0.5s ease-in 2.5s;
    font-weight: 500;
    max-width: 300px;
  `;

    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
  }

  // Adicionar animação CSS
  const style = document.createElement("style");
  style.textContent = `
  @keyframes fadeInOut {
    0%, 100% { opacity: 0; transform: translateX(100%); }
    20%, 80% { opacity: 1; transform: translateX(0); }
  }
  
  @keyframes slideInRight {
    from { opacity: 0; transform: translateX(100%); }
    to { opacity: 1; transform: translateX(0); }
  }
  
  @keyframes slideOutRight {
    from { opacity: 1; transform: translateX(0); }
    to { opacity: 0; transform: translateX(100%); }
  }
`;
  document.head.appendChild(style);

  // Sistema de temas
  document.addEventListener("DOMContentLoaded", function () {
    // Carregar tema salvo
    const savedTheme = localStorage.getItem("tema") || "azul";
    applyTheme(savedTheme);

    // Marcar o tema atual como selecionado
    const currentThemeRadio = document.querySelector(
      `input[name="tema"][value="${savedTheme}"]`
    );
    if (currentThemeRadio) {
      currentThemeRadio.checked = true;
      currentThemeRadio.closest(".theme-option").classList.add("selected");
    }

    // Listener para mudança de tema
    document.querySelectorAll('input[name="tema"]').forEach((radio) => {
      radio.addEventListener("change", function () {
        if (this.checked) {
          const theme = this.value;
          applyTheme(theme);
          localStorage.setItem("tema", theme);

          // Atualizar seleção visual
          document.querySelectorAll(".theme-option").forEach((option) => {
            option.classList.remove("selected");
          });
          this.closest(".theme-option").classList.add("selected");

          showNotification(` Tema ${theme} aplicado!`, "success");
        }
      });
    });

    // Função para aplicar tema
    function applyTheme(theme) {
      document.documentElement.setAttribute("data-theme", theme);

      // Aplicar cores específicas baseadas no tema
      const themes = {
        azul: { primary: "#3b8d9e", secondary: "#0056b3" },
        verde: { primary: "#28a745", secondary: "#20c997" },
        roxo: { primary: "#6f42c1", secondary: "#563d7c" },
        vermelho: { primary: "#dc3545", secondary: "#c82333" },
        escuro: { primary: "#343a40", secondary: "#495057" },
      };

      if (themes[theme]) {
        document.documentElement.style.setProperty(
          "--primary-color",
          themes[theme].primary
        );
        document.documentElement.style.setProperty(
          "--secondary-color",
          themes[theme].secondary
        );
      }
    }
  });
 