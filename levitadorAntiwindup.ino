// ------------------------------
// CONFIGURACION DE PINES
// ------------------------------
const int trigPin = 12;
const int echoPin = 11;

const int enPin = 9;
const int in1  = 8;
const int in2  = 7;

// ------------------------------
// CONTROL
// ------------------------------
float setpoint = 0.0;
const float alturaSensor = 57.0;

float Kp;
float Ki;
float Kd;

unsigned long previous_time = 0;

float accumulated_error = 0;
float output = 0;
float last_error = 0;

float error;

// Limite para el ANTIWINDUP
const float MAX_INTEGRAL = 50.0;  

String inputString = "";
bool stringComplete = false;

// ------------------------------
// ULTRASONICO
// ------------------------------
long medirUltrasonico() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duracion = pulseIn(echoPin, HIGH, 25000);
  return duracion * 0.0343 / 2;
}

// ------------------------------
// MOTOR
// ------------------------------
void moverMotor(float pwm) {
  if (pwm > 0) {
    digitalWrite(in1, HIGH);
    digitalWrite(in2, LOW);
  } 
  else if (pwm < 0) {
    digitalWrite(in1, LOW);
    digitalWrite(in2, HIGH);
  } 
  else {
    digitalWrite(in1, LOW);
    digitalWrite(in2, LOW);
  }

  analogWrite(enPin, constrain(abs(pwm), 0, 255));
}

// ------------------------------
// PROCESAR COMANDO
// ------------------------------
void procesarComando() {
  inputString.trim();
  if (inputString.length() == 0) return;

  // -----------------------------------------
  // Comando en formato "30,12,0.8,4"
  // -----------------------------------------

  int c1 = inputString.indexOf(',');
  int c2 = inputString.indexOf(',', c1 + 1);
  int c3 = inputString.indexOf(',', c2 + 1);

  if (c1 != -1 && c2 != -1 && c3 != -1) {
    String sSet = inputString.substring(0, c1);
    String sKp  = inputString.substring(c1 + 1, c2);
    String sKi  = inputString.substring(c2 + 1, c3);
    String sKd  = inputString.substring(c3 + 1);

    float newSet = sSet.toFloat();
    float newKp  = sKp.toFloat();
    float newKi  = sKi.toFloat();
    float newKd  = sKd.toFloat();

    //  Reset del integrador solo al cambiar setpoint
    if (newSet > 0 && newSet < 65 && newSet != setpoint) {
      accumulated_error = 0;  // Reset porque cambió el objetivo
      Serial.println("*** Integral reseteado (cambio de setpoint) ***");
      setpoint = newSet;
    }
    else if (newSet > 0 && newSet < 65) {
      setpoint = newSet;
    }

    Kp = newKp;
    Ki = newKi;
    Kd = newKd;

    Serial.println("\n--- PARÁMETROS ACTUALIZADOS (formato CSV) ---");
    Serial.print("SP = "); Serial.println(setpoint);
    Serial.print("Kp = "); Serial.println(Kp);
    Serial.print("Ki = "); Serial.println(Ki);
    Serial.print("Kd = "); Serial.println(Kd);
    Serial.println("--------------------------------------------\n");

    inputString = "";
    return;
  }

  Serial.println("Formato no válido.");
  inputString = "";
}

// ------------------------------
// SETUP
// ------------------------------
void setup() {
  Serial.begin(9600);

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  pinMode(enPin, OUTPUT);
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);

  previous_time = millis();

  Serial.println("==============================================");
  Serial.println("  SISTEMA PID CON ANTIWINDUP");
  Serial.println("==============================================");
  Serial.println("Formatos válidos:");
  Serial.println("  30,12,0.8,4   (SP,KP,KI,KD)");
  Serial.println();
  Serial.print("Límite integral: ±");
  Serial.println(MAX_INTEGRAL);
  Serial.println("==============================================\n");
}

// ------------------------------
// LOOP
// ------------------------------
void loop() {

  // LECTURA DE SERIAL
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') procesarComando();
    else inputString += c;
  }

  // LECTURA ULTRASONICO
  float lecturaSensor = medirUltrasonico();
  float posicion = alturaSensor - lecturaSensor;

  // -----------------------------------------
  // PID (Ejecutado cada 15 ms)
  // -----------------------------------------
  unsigned long current_time = millis();

  if (current_time - previous_time >= 15) {

    // Error
    error = setpoint - posicion;

    // P
    float P = Kp * error;

    // I c
    accumulated_error += error * 0.015;   
    
    // Constrain que limita el error para evitar saltos bruscos (De -50 a 50)
    accumulated_error = constrain(accumulated_error, -MAX_INTEGRAL, MAX_INTEGRAL);
    
    float I = Ki * accumulated_error;

    // D
    float derivative = (error - last_error) / 0.015;
    float D = Kd * derivative;
    last_error = error;

    // Salida PID
    output = P + I + D;
    output = constrain(output, -255, 255);

    // Enviar al motor
    moverMotor(output);

    // Actualizar tiempo
    previous_time = current_time;
  }

  // MONITOREO
  Serial.print("Posicion: ");
  Serial.print(posicion);
  Serial.print(" | PWM: ");
  Serial.print(output);
  Serial.print(" | SP=");
  Serial.print(setpoint);
  Serial.print(" | Kp=");
  Serial.print(Kp);
  Serial.print(" Ki=");
  Serial.print(Ki);
  Serial.print(" Kd=");
  Serial.print(Kd);
  Serial.print(" | AccErr=");
  Serial.println(accumulated_error);  
  Serial.println(error);

  delay(40);
}
