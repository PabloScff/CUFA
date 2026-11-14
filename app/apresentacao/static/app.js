/* Comportamento mínimo no cliente. Toda validação estrita é refeita no servidor (Pydantic). */
(function () {
  "use strict";

  // Máscaras para agilizar a digitação em campo
  function soDigitos(v) { return v.replace(/\D/g, ""); }
  var mascaras = {
    cpf: function (v) {
      var d = soDigitos(v).slice(0, 11);
      return d.replace(/^(\d{3})(\d)/, "$1.$2").replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3").replace(/\.(\d{3})(\d)/, ".$1-$2");
    },
    telefone: function (v) {
      var d = soDigitos(v).slice(0, 11);
      if (d.length <= 2) return d ? "(" + d : "";
      if (d.length <= 6) return "(" + d.slice(0, 2) + ") " + d.slice(2);
      if (d.length <= 10) return "(" + d.slice(0, 2) + ") " + d.slice(2, 6) + "-" + d.slice(6);
      return "(" + d.slice(0, 2) + ") " + d.slice(2, 7) + "-" + d.slice(7);
    }
  };
  document.querySelectorAll("[data-mascara]").forEach(function (campo) {
    var fn = mascaras[campo.dataset.mascara];
    if (!fn) return;
    campo.addEventListener("input", function () { campo.value = fn(campo.value); });
    if (campo.value) campo.value = fn(campo.value);
  });

  // Mostrar/ocultar senha (alvo de toque de 44px+)
  document.querySelectorAll("[data-mostrar-senha]").forEach(function (caixa) {
    caixa.addEventListener("change", function () {
      var alvo = document.getElementById(caixa.dataset.mostrarSenha);
      if (alvo) alvo.type = caixa.checked ? "text" : "password";
    });
  });

  // Evita toque duplo: desabilita o botão enquanto o registro é enviado
  document.querySelectorAll("form[data-uma-vez]").forEach(function (form) {
    form.addEventListener("submit", function () {
      var botao = form.querySelector("button[type=submit]");
      if (botao) { botao.disabled = true; botao.textContent = "Registrando…"; }
    });
  });
  window.addEventListener("pageshow", function (e) {  // voltar pelo navegador restaura o botão
    if (!e.persisted) return;
    document.querySelectorAll("form[data-uma-vez] button[type=submit]").forEach(function (b) {
      b.disabled = false; b.textContent = "Validar e Registrar Entrega";
    });
  });

  // Tela 3: feedback pelo tato além de cor, ícone e texto (1 pulso = sucesso, 3 pulsos = bloqueio)
  var resultado = document.querySelector("[data-vibrar]");
  if (resultado && navigator.vibrate) {
    navigator.vibrate(resultado.dataset.vibrar === "sucesso" ? [120] : [250, 120, 250, 120, 250]);
  }
})();
