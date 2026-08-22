document.addEventListener("DOMContentLoaded", () => {
    // Mobile Menu Toggle logic
    const mobileMenuToggle = document.getElementById("mobileMenuToggle");
    const mobileMenu = document.getElementById("mobileMenu");

    if (mobileMenuToggle && mobileMenu) {
        mobileMenuToggle.addEventListener("click", () => {
            const isHidden = mobileMenu.classList.contains("hidden");
            if (isHidden) {
                mobileMenu.classList.remove("hidden");
                mobileMenuToggle.setAttribute("aria-expanded", "true");
            } else {
                mobileMenu.classList.add("hidden");
                mobileMenuToggle.setAttribute("aria-expanded", "false");
            }
        });
    }

    // Smooth scroll navigation handler for mobile links closure
    const mobileLinks = document.querySelectorAll(".serene-mobile-link");
    mobileLinks.forEach(link => {
        link.addEventListener("click", () => {
            if (mobileMenu) mobileMenu.classList.add("hidden");
        });
    });

    // Clean client-side Contact Form Handler
    const contactForm = document.getElementById("studioContactForm");
    const contactStatus = document.getElementById("contactStatus");

    if (contactForm) {
        contactForm.addEventListener("submit", (e) => {
            e.preventDefault();
            
            // Basic Form Validation
            if (!contactForm.checkValidity()) {
                contactStatus.textContent = "Please fill out all fields correctly.";
                contactStatus.style.color = "red";
                return;
            }

            contactStatus.textContent = "Sending your message...";
            contactStatus.style.color = "var(--text-color)";

            // Simulated Successful Submission
            setTimeout(() => {
                contactStatus.textContent = "Thank you! Your message has been sent successfully.";
                contactStatus.style.color = "green";
                contactForm.reset();
            }, 1000);
        });
    }
});

// FIXED: Exact AI Endpoint Target
const BACKEND_API_URL = "/handle-message";

function toggleChat() {
  const windowEl = document.getElementById("ai-chat-window");
  const openIcon = document.getElementById("ai-icon-open");
  const closeIcon = document.getElementById("ai-icon-close");

  if (windowEl.style.display === "none" || windowEl.style.display === "") {
    windowEl.style.display = "flex";
    openIcon.style.display = "none";
    closeIcon.style.display = "block";
  } else {
    windowEl.style.display = "none";
    openIcon.style.display = "block";
    closeIcon.style.display = "none";
  }
}

async function sendChatMessage() {
  const inputEl = document.getElementById("ai-user-input");
  const messagesEl = document.getElementById("ai-chat-messages");
  const userMessage = inputEl.value.trim();

  if (!userMessage) return;

  const userMsgDiv = document.createElement("div");
  userMsgDiv.className = "ai-message ai-user";
  userMsgDiv.textContent = userMessage;
  messagesEl.appendChild(userMsgDiv);

  inputEl.value = "";
  messagesEl.scrollTop = messagesEl.scrollHeight;

  const loadingDiv = document.createElement("div");
  loadingDiv.className = "ai-message ai-bot";
  loadingDiv.id = "ai-loading-indicator";
  loadingDiv.innerHTML = `<div class="ai-loading-dots"><span></span><span></span><span></span></div>`;
  messagesEl.appendChild(loadingDiv);
  messagesEl.scrollTop = messagesEl.scrollHeight;

  try {
    const response = await fetch(BACKEND_API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_name: "Visitor",
        message: userMessage
      })
    });

    const data = await response.json();
    
    const indicator = document.getElementById("ai-loading-indicator");
    if (indicator) indicator.remove();

    const botMsgDiv = document.createElement("div");
    botMsgDiv.className = "ai-message ai-bot";
    botMsgDiv.textContent = data.reply || "Something went wrong.";
    messagesEl.appendChild(botMsgDiv);

  } catch (error) {
    const indicator = document.getElementById("ai-loading-indicator");
    if (indicator) indicator.remove();

    const errorMsgDiv = document.createElement("div");
    errorMsgDiv.className = "ai-message ai-bot";
    errorMsgDiv.style.color = "#f87171";
    errorMsgDiv.textContent = "Connection lost. Please check server connection.";
    messagesEl.appendChild(errorMsgDiv);
  }

  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function handleKeyPress(event) {
  if (event.key === "Enter") {
    event.preventDefault(); // Prevents page reload
    sendChatMessage();
  }
}