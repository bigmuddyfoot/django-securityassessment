document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ admin_questioninputoption.js loaded");
  
    function attachPreferredLimitLogic() {
      const checkboxes = document.querySelectorAll(
        'input[type="checkbox"][name$="-is_preferred"]'
      );
  
      checkboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", function () {
          if (this.checked) {
            const tbody = this.closest("tbody");
            const allCheckboxes = tbody.querySelectorAll('input[type="checkbox"][name$="-is_preferred"]');
            allCheckboxes.forEach((cb) => {
              if (cb !== this) cb.checked = false;
            });
          }
        });
      });
    }
  
    attachPreferredLimitLogic();
  
    // Re-attach logic when a new inline is added
    document.body.addEventListener("click", function (event) {
      if (event.target && event.target.classList.contains("add-row")) {
        setTimeout(attachPreferredLimitLogic, 100);
      }
    });
  });
  