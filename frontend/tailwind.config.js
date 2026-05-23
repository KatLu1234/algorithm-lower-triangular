/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // 기본 팔레트: 마룬(#7C001A) + 크림(#F6F3EE). product.md §3.1 — 정돈된·신뢰감.
        // brand = 마룬 스케일 (600이 지정 색).
        brand: {
          50: "#FBEDEF",
          100: "#F6D9DD",
          200: "#EAB2BB",
          300: "#DA8290",
          400: "#C2455C",
          500: "#9E1A35",
          600: "#7C001A",
          700: "#660016",
          800: "#500012",
          900: "#3E000E",
        },
        // cream = 따뜻한 배경/표면 (100이 지정 색).
        cream: {
          DEFAULT: "#F6F3EE",
          50: "#FBFAF7",
          100: "#F6F3EE",
          200: "#ECE5DA",
          300: "#DCD2C3",
        },
        // 크림 배경에 어울리는 따뜻한 중립 텍스트.
        ink: {
          DEFAULT: "#292524",
          soft: "#57534E",
          faint: "#A8A29E",
        },
      },
      fontFamily: {
        sans: [
          "Pretendard",
          "Apple SD Gothic Neo",
          "Noto Sans KR",
          "system-ui",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};
