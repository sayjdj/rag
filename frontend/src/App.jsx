import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';

const API_URL = process.env.NODE_ENV === 'development' ? 'http://localhost:5000/api/rage' : 'https://api-placeholder.com/api/rage'; // 배포 시엔 일단 콘솔에만 찍히거나 무시되게 임시 처리

function App() {
  const [clickCount, setClickCount] = useState(0);
  const startTime = useRef(Date.now());
  const [errorMsg, setErrorMsg] = useState("");

  // Form states
  const [nameLetters, setNameLetters] = useState(["", "", ""]); // 이름 3글자
  const [phone, setPhone] = useState(0);
  const [password, setPassword] = useState("");
  const [agreed, setAgreed] = useState(false);

  // Running button states
  const [btnPos, setBtnPos] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const reportRage = async (action, details = "") => {
    try {
      // GitHub Pages 배포 시 backend는 localhost이거나 없을 수 있으므로 try-catch로 무시
      await axios.post(API_URL, {
        action,
        clicks: clickCount,
        timeSpent: Date.now() - startTime.current,
        details
      }).catch(() => { /* ignore cors/network errors on github pages */ });
    } catch (e) {
      // ignore
    }
  };

  const handleGlobalClick = () => {
    setClickCount(c => c + 1);
  };

  useEffect(() => {
    window.addEventListener('click', handleGlobalClick);
    return () => window.removeEventListener('click', handleGlobalClick);
  }, []);

  const moveButton = () => {
    setIsHovered(true);
    setBtnPos({
      x: Math.random() * 300 - 150,
      y: Math.random() * 300 - 150
    });
    reportRage("button_hovered", "User tried to click submit");
  };

  const isPrime = (num) => {
    for(let i = 2, s = Math.sqrt(num); i <= s; i++) {
        if(num % i === 0) return false;
    }
    return num > 1;
  };

  const checkPasswordHasPrime = (pw) => {
    const numbers = pw.match(/\d+/g);
    if (!numbers) return false;
    for (let numStr of numbers) {
      if (isPrime(parseInt(numStr))) return true;
    }
    return false;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setClickCount(c => c + 1);

    if (nameLetters.includes("")) {
      setErrorMsg("당신의 잘못입니다. 이름을 끝까지 선택하세요.");
      reportRage("submit_failed", "Missing name");
      return;
    }

    if (!checkPasswordHasPrime(password)) {
      setErrorMsg("당신의 잘못입니다. 비밀번호에 랜덤한 소수(Prime Number)가 포함되어야 합니다.");
      reportRage("submit_failed", "Password no prime");
      return;
    }

    if (!agreed) {
      setErrorMsg("당신의 잘못입니다. 동의란에 체크하지 않았습니다.");
      reportRage("submit_failed", "Not agreed");
      return;
    }

    alert("가입 성공! 사실 서버에는 저장되지 않았습니다. 분노해주셔서 감사합니다.");
    reportRage("submit_success", "User somehow did it");
  };

  const alphabets = "ABCDEFGHIJKLMNOPQRSTUVWXYZ가나다라마바사아자차카타파하".split('');

  const toggleAgree = () => {
    setAgreed(!agreed);
    if (Math.random() > 0.3) {
      setTimeout(() => {
        setAgreed(false);
        reportRage("checkbox_unchecked_randomly");
      }, 500);
    }
  };

  return (
    <div className="container no-select">
      <marquee direction="right" scrollamount="15" className="text-3xl font-bold blink mb-4 bg-yellow-300 text-red-600">
        🔥 웰컴 투 환장 회원가입 🔥
      </marquee>

      <h1 className="text-2xl mb-6 bg-black text-white p-2 border-4 border-dashed border-red-500">
        아주 "간단한" 회원가입 양식
      </h1>

      {errorMsg && (
        <div className="bg-red-600 text-yellow-300 p-4 border-8 border-yellow-400 mb-4 animate-bounce font-black text-xl">
          {errorMsg}
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex flex-col gap-6 text-left">

        {/* 1. 이름 드롭다운 */}
        <div className="bg-blue-300 p-4 border-2 border-white">
          <label className="block font-bold mb-2 text-blue-900">1. 이름 (드롭다운으로 한 글자씩 선택)</label>
          <div className="flex gap-2">
            {[0, 1, 2].map(idx => (
              <select
                key={idx}
                value={nameLetters[idx]}
                onChange={e => {
                  const newName = [...nameLetters];
                  newName[idx] = e.target.value;
                  setNameLetters(newName);
                  reportRage("name_select");
                }}
                className="p-2 w-20 text-center"
              >
                <option value="">?</option>
                {alphabets.sort(() => Math.random() - 0.5).map((char, i) => (
                  <option key={i} value={char}>{char}</option>
                ))}
              </select>
            ))}
          </div>
          <p className="text-xs mt-1 text-gray-700">순서가 계속 바뀝니다. 행운을 빕니다.</p>
        </div>

        {/* 2. 전화번호 슬라이더 */}
        <div className="bg-green-300 p-4 border-2 border-white">
          <label className="block font-bold mb-2 text-green-900">
            2. 전화번호: <span className="bg-black text-green-400 p-1">010-{String(phone).padStart(8, '0')}</span>
          </label>
          <input
            type="range"
            min="0"
            max="99999999"
            value={phone}
            onChange={(e) => {
              setPhone(e.target.value);
              if (Math.random() > 0.95) reportRage("slider_adjust");
            }}
            className="w-full h-2 bg-red-400 rounded-lg appearance-none cursor-pointer"
          />
          <p className="text-xs mt-1 text-gray-700">미세한 컨트롤을 요구합니다. (직접 입력 불가)</p>
        </div>

        {/* 3. 소수 비밀번호 */}
        <div className="bg-purple-300 p-4 border-2 border-white">
          <label className="block font-bold mb-2 text-purple-900">3. 비밀번호</label>
          <input
            type="text" // 의도적으로 text로 보여줌
            value={password}
            onChange={e => setPassword(e.target.value)}
            className="w-full p-2 border-b-4 border-red-500 bg-yellow-100"
            placeholder="반드시 '소수(Prime Number)'를 포함하세요"
          />
        </div>

        {/* 4. 약관 동의 (랜덤 해제) */}
        <div className="bg-orange-300 p-4 border-2 border-white flex items-center gap-3">
          <input
            type="checkbox"
            checked={agreed}
            onChange={toggleAgree}
            className="w-6 h-6"
          />
          <label className="font-bold text-red-900 blinking">
            [필수] 내 영혼을 개발자에게 귀속시킴에 동의합니다.
          </label>
        </div>

        {/* 5. 도망가는 버튼 */}
        <div className="relative h-40 flex justify-center items-center mt-4">
          <motion.button
            type="submit"
            animate={{ x: btnPos.x, y: btnPos.y }}
            onHoverStart={moveButton}
            onClick={() => setClickCount(c => c + 1)}
            transition={{ type: "spring", stiffness: 300, damping: 10 }}
            className="absolute px-8 py-4 bg-green-500 text-white font-black text-2xl border-4 border-black"
          >
            가입하기 (할 수 있다면)
          </motion.button>
        </div>
      </form>

      <div className="fixed bottom-2 right-2 text-xs bg-black text-red-500 p-1 font-mono">
        Rage Clicks: {clickCount}
      </div>
    </div>
  );
}

export default App;
